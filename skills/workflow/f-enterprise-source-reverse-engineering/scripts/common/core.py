"""Small, dependency-free primitives used by all indexers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

EXCLUDED_DIRS = {".git", ".idea", ".vscode", "vendor", "node_modules", "runtime", "cache", "tmp", "logs", "coverage", "dist", "build", "uploads"}
SOURCE_EXTENSIONS = {".php", ".inc", ".phtml", ".sql", ".yaml", ".yml", ".json", ".xml", ".ini", ".env", ".twig"}
MODULE_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


def validate_module_name(value: str) -> str:
    if not MODULE_NAME.fullmatch(value):
        raise ValueError("module must be 1-64 lowercase letters, digits, or hyphens")
    return value


def validate_analysis_run_id(value: str, project: str, module: str) -> str:
    pattern = re.compile(rf"^{re.escape(project)}-{re.escape(module)}-[0-9]{{8}}-[0-9]{{3}}$")
    if not pattern.fullmatch(value):
        raise ValueError(f"analysis run ID must match {project}-{module}-YYYYMMDD-NNN")
    return value

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def file_fingerprint(path: Path) -> tuple[str, int, os.stat_result]:
    """Hash and count lines from one stable file snapshot, retrying active writes."""
    for _ in range(3):
        before = path.stat()
        digest = hashlib.sha256()
        newline_count = 0
        size = 0
        last = b""
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
                newline_count += chunk.count(b"\n")
                size += len(chunk)
                last = chunk[-1:]
        after = path.stat()
        if before.st_size == after.st_size == size and before.st_mtime_ns == after.st_mtime_ns:
            line_count = newline_count + (1 if size and last != b"\n" else 0)
            return digest.hexdigest(), line_count, after
    raise RuntimeError(f"file changed repeatedly while indexing: {path}")

def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _process_exists(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return kernel32.GetLastError() == 5
        try:
            exit_code = wintypes.DWORD()
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return True


@contextmanager
def exclusive_lock(path: Path, timeout: float = 30.0) -> Iterator[None]:
    """Use portable O_EXCL locks and recover locks whose owning process exited."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(f".{path.name}.lock")
    deadline = time.monotonic() + timeout
    descriptor: int | None = None
    token = uuid.uuid4().hex
    while descriptor is None:
        try:
            descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            payload = json.dumps({"pid": os.getpid(), "token": token, "created_at": time.time()})
            os.write(descriptor, payload.encode("ascii"))
        except FileExistsError:
            try:
                owner = json.loads(lock.read_text(encoding="ascii"))
                pid = int(owner["pid"])
                if not _process_exists(pid):
                    lock.unlink(missing_ok=True)
                    continue
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for index lock: {lock}")
            time.sleep(0.05)
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            owner = json.loads(lock.read_text(encoding="ascii"))
            if owner.get("token") == token:
                lock.unlink()
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass

def ensure_outside_source(output: Path, source_root: Path) -> None:
    """Reject output paths inside the analyzed source tree."""
    resolved_output = output.resolve(strict=False)
    resolved_root = source_root.resolve()
    if resolved_output == resolved_root or resolved_root in resolved_output.parents:
        raise ValueError(f"output path must be outside analyzed source root: {resolved_output}")


def _manifest_root(workspace: Path, project: str) -> Path | None:
    manifest = workspace / "indexes" / project / "index-manifest.json"
    if not manifest.is_file():
        return None
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {project} index manifest: {exc}") from exc
    if value.get("project") != project or not isinstance(value.get("repository_root"), str):
        raise ValueError(f"invalid {project} project/root binding in index manifest")
    return Path(value["repository_root"]).resolve(strict=False)


def validate_source_snapshot(workspace: Path, project: str, snapshot_id: str) -> dict[str, Any]:
    """Verify an explicit source snapshot token without rereading project source files."""
    manifest_path = workspace / "indexes" / project / "index-manifest.json"
    source_path = workspace / "indexes" / project / "source-index.jsonl"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid source snapshot manifest: {exc}") from exc
    if manifest.get("project") != project or manifest.get("snapshot_id") != snapshot_id:
        raise ValueError("source snapshot ID does not match the current project manifest")
    expected_hash = manifest.get("source_index_sha256")
    if not isinstance(expected_hash, str) or sha256_file(source_path) != expected_hash:
        raise ValueError("source index changed after the trusted snapshot was created")
    return manifest


def ensure_project_root_binding(workspace: Path, project: str, root: Path) -> None:
    """Bind A/B to distinct immutable roots within one analysis workspace."""
    resolved = root.resolve()
    current = _manifest_root(workspace, project)
    if current is not None and current != resolved:
        raise ValueError(f"Project {project} is already bound to repository root: {current}")
    other = "B" if project == "A" else "A"
    other_root = _manifest_root(workspace, other)
    if other_root is not None and other_root == resolved:
        raise ValueError(f"repository root is already bound to Project {other}: {resolved}")


def load_isolated_source_index(
    workspace: Path,
    project: str,
    expected_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Load one project's source rows only after validating project and path boundaries."""
    path = workspace / "indexes" / project / "source-index.jsonl"
    rows = read_jsonl(path)
    if not rows:
        raise ValueError(f"source index is missing or empty: {path}")
    roots: set[Path] = set()
    for position, row in enumerate(rows):
        if row.get("project") != project:
            raise ValueError(f"source index project mismatch at row {position}")
        relative = row.get("relative_path")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"invalid source relative path at row {position}")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"source path escapes project root at row {position}: {relative}")
        root = Path(row.get("repository_root", "")).resolve(strict=False)
        absolute = Path(row.get("absolute_path", "")).resolve(strict=False)
        expected = (root / Path(*pure.parts)).resolve(strict=False)
        if absolute != expected or (absolute != root and root not in absolute.parents):
            raise ValueError(f"source absolute path escapes project root at row {position}: {relative}")
        roots.add(root)
    if len(roots) != 1:
        raise ValueError(f"Project {project} source index has {len(roots)} repository roots")
    root = next(iter(roots))
    bound = _manifest_root(workspace, project)
    if bound is None or bound != root:
        raise ValueError(f"Project {project} source index does not match its root binding")
    if expected_root is not None and root != expected_root.resolve():
        raise ValueError(f"Project {project} root does not match indexed root: {root}")
    other = "B" if project == "A" else "A"
    other_root = _manifest_root(workspace, other)
    if other_root is not None and other_root == root:
        raise ValueError(f"Projects A and B share repository root: {root}")
    return rows

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSONL: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: record must be an object")
            rows.append(value)
    return rows


def read_project_jsonl(path: Path, project: str) -> list[dict[str, Any]]:
    rows = read_jsonl(path)
    for position, row in enumerate(rows):
        if row.get("project") != project:
            raise ValueError(f"{path.name}:{position}: project mismatch")
    return rows

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    atomic_write(path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))

def locked_jsonl_update(path: Path, updater: Any) -> list[dict[str, Any]]:
    with exclusive_lock(path):
        rows = updater(read_jsonl(path))
        write_jsonl(path, rows)
        return rows

def iter_source_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")
    for current, directories, files in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix.lower() in SOURCE_EXTENSIONS or path.name.startswith(".env"):
                yield path

def text_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()

def source_record(project: str, root: Path, path: Path, old: dict[str, Any] | None = None) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    digest, line_count, stat = file_fingerprint(path)
    previous_hash = old.get("sha256") if old else None
    record: dict[str, Any] = {
        "project": project, "repository_root": str(root.resolve()), "relative_path": relative,
        "absolute_path": str(path.resolve()), "language": language_for(path), "extension": path.suffix,
        "size_bytes": stat.st_size, "line_count": line_count, "sha256": digest,
        "previous_sha256": previous_hash if previous_hash and previous_hash != digest else (old or {}).get("previous_sha256"),
        "mtime": stat.st_mtime, "mtime_ns": stat.st_mtime_ns, "directory_role": directory_role(relative),
        "analysis_status": "STALE" if previous_hash and previous_hash != digest else (old or {}).get("analysis_status", "UNREAD"),
        "modules": (old or {}).get("modules", []), "symbols": (old or {}).get("symbols", []),
        "routes": (old or {}).get("routes", []), "tables": (old or {}).get("tables", []),
        "config_keys": (old or {}).get("config_keys", []), "external_services": (old or {}).get("external_services", []),
        "references": (old or {}).get("references", []), "referenced_by": (old or {}).get("referenced_by", []),
        "first_indexed_at": (old or {}).get("first_indexed_at"), "last_indexed_at": None,
        "last_analyzed_at": (old or {}).get("last_analyzed_at"), "notes": (old or {}).get("notes", []),
    }
    return record

def language_for(path: Path) -> str:
    return {".php": "PHP", ".sql": "SQL", ".yaml": "YAML", ".yml": "YAML", ".json": "JSON", ".xml": "XML"}.get(path.suffix.lower(), "TEXT")

def directory_role(relative: str) -> str:
    parts = relative.split("/")
    return parts[-2].lower() if len(parts) > 1 else "root"

PHP_TYPE = r"[?\\A-Za-z_][\\A-Za-z0-9_|?]*"
PHP_CLASS = re.compile(
    r"\b(class|interface|trait)\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+extends\s+([A-Za-z_\\][A-Za-z0-9_\\]*))?"
    r"(?:\s+implements\s+([^\{]+))?"
)
PHP_METHOD = re.compile(r"(?P<mods>(?:(?:public|protected|private|static|final|abstract)\s+)*)function\s+&?\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<params>[^)]*)\)")
PHP_NAMESPACE = re.compile(r"^\s*namespace\s+([^;]+);", re.MULTILINE)
PHP_USE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
PHP_BUILTIN_TYPES = {"array", "bool", "callable", "false", "float", "int", "iterable", "mixed", "never", "null", "object", "parent", "self", "static", "string", "true", "void"}

def _symbol_end(lines: list[str], start: int) -> int:
    depth = 0
    opened = False
    for index in range(start - 1, len(lines)):
        for character in lines[index]:
            if character == "{":
                depth += 1
                opened = True
            elif character == "}" and opened:
                depth -= 1
                if depth == 0:
                    return index + 1
    return len(lines)

def _short_type(value: str) -> str:
    return value.lstrip("?\\").split("\\")[-1]


def _parameter_types(parameters: list[str], imports: dict[str, str], namespace: str) -> list[str]:
    resolved = []
    for parameter in parameters:
        match = re.search(rf"({PHP_TYPE})\s+(?:&\s*)?\$[A-Za-z_][A-Za-z0-9_]*", parameter)
        if not match:
            continue
        for type_name in match.group(1).lstrip("?").split("|"):
            short = _short_type(type_name)
            if short.lower() in PHP_BUILTIN_TYPES:
                continue
            resolved.append(imports.get(short, type_name.lstrip("\\") if "\\" in type_name else f"{namespace}\\{short}" if namespace else short))
    return sorted(set(resolved))

def extract_php_symbols(path: Path, project: str, root: Path) -> list[dict[str, Any]]:
    lines = text_lines(path)
    text = "\n".join(lines)
    namespace_match = PHP_NAMESPACE.search(text)
    namespace = namespace_match.group(1).strip() if namespace_match else ""
    digest = sha256_file(path)
    relative = path.relative_to(root).as_posix()
    imports = {item.split("\\")[-1]: item for item in PHP_USE.findall(text)}
    class_match = PHP_CLASS.search(text)
    class_name = class_match.group(2) if class_match else None
    class_fqn = f"{namespace}\\{class_name}" if namespace and class_name else class_name
    extends = None
    implements: list[str] = []
    if class_match:
        if class_match.group(3):
            short = _short_type(class_match.group(3))
            extends = imports.get(short, class_match.group(3).lstrip("\\"))
        if class_match.group(4):
            for interface in class_match.group(4).split(","):
                short = _short_type(interface.strip())
                implements.append(imports.get(short, interface.strip().lstrip("\\")))
    property_types: dict[str, str] = {}
    for type_name, property_name in re.findall(rf"(?:public|protected|private)\s+({PHP_TYPE})\s+\$([A-Za-z_][A-Za-z0-9_]*)", text):
        short = _short_type(type_name)
        property_types[property_name] = imports.get(short, f"{namespace}\\{short}" if namespace else short)
    records: list[dict[str, Any]] = []
    if class_match and class_name and class_fqn:
        line = text.count("\n", 0, class_match.start()) + 1
        model_tables = sorted(set(re.findall(r"\$table\s*=\s*['\"]([^'\"]+)['\"]", text)))
        records.append({"project": project, "symbol_id": f"{project}:{relative}:{class_fqn}", "file": relative, "file_sha256": digest, "namespace": namespace, "container_symbol": class_fqn, "symbol_type": class_match.group(1), "name": class_name, "fully_qualified_name": class_fqn, "extends": extends, "implements": sorted(set(implements)), "start_line": line, "end_line": _symbol_end(lines, line), "visibility": "public", "parameters": [], "return_type": None, "calls": [], "called_by": [], "tables": model_tables, "routes": [], "modules": [], "analysis_status": "PARTIAL", "notes": []})
    for match in PHP_METHOD.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        end = _symbol_end(lines, line)
        name = match.group("name")
        fqn = f"{class_fqn}::{name}" if class_fqn else f"{namespace}\\{name}" if namespace else name
        body = "\n".join(lines[line - 1:end])
        calls: list[str] = []
        for prop, method in re.findall(r"\$this->([A-Za-z_][A-Za-z0-9_]*)->([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            target = property_types.get(prop, f"$this->{prop}")
            calls.append(f"{target}::{method}")
        for target, method in re.findall(r"\b([A-Za-z_\\][A-Za-z0-9_\\]*)::([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            resolved = imports.get(_short_type(target), target.lstrip("\\"))
            calls.append(f"{resolved}::{method}")
        for method in re.findall(r"\$this->([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            if class_fqn:
                calls.append(f"{class_fqn}::{method}")
        modifiers = match.group("mods").split()
        parameters = [part.strip() for part in match.group("params").split(",") if part.strip()]
        parameter_types = _parameter_types(parameters, imports, namespace)
        tables = sorted(set(re.findall(r"(?:table|from)\s*\(\s*['\"]([^'\"]+)", body, re.I)))
        records.append({"project": project, "symbol_id": f"{project}:{relative}:{fqn}", "file": relative, "file_sha256": digest, "namespace": namespace, "container_symbol": class_fqn, "symbol_type": "method" if class_fqn else "function", "name": name, "fully_qualified_name": fqn, "start_line": line, "end_line": end, "visibility": next((item for item in modifiers if item in {"public", "protected", "private"}), "public"), "parameters": parameters, "parameter_types": parameter_types, "return_type": None, "calls": sorted(set(calls)), "called_by": [], "tables": tables, "routes": [], "modules": [], "analysis_status": "PARTIAL", "notes": ["PARSER_LIMITATION: conservative token/regex extraction; verify dynamic calls manually"]})
    return records

def line_range_exists(path: Path, start: int, end: int) -> bool:
    count = len(text_lines(path))
    return 1 <= start <= end <= count
