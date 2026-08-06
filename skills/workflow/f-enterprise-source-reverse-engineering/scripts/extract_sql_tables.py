#!/usr/bin/env python3
"""Extract CREATE TABLE definitions from project SQL or workspace snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common.core import (
    atomic_write,
    ensure_outside_source,
    exclusive_lock,
    iter_source_files,
    load_isolated_source_index,
    read_project_jsonl,
    write_jsonl,
)


TABLE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([A-Za-z0-9_.$-]+)", re.I)
PROJECT_SOURCE = "PROJECT_SOURCE"
EXTERNAL_SQL_SNAPSHOT = "EXTERNAL_SQL_SNAPSHOT"
EXTERNAL_SQL_NOTE = "外部数据库快照；文件位于源码根目录之外，不参与 source-index 链接校验"


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _record_scope(row: dict) -> str:
    if row.get("source_scope") in {PROJECT_SOURCE, EXTERNAL_SQL_SNAPSHOT}:
        return row["source_scope"]
    notes = row.get("notes")
    if isinstance(notes, list) and EXTERNAL_SQL_NOTE in notes:
        return EXTERNAL_SQL_SNAPSHOT
    return PROJECT_SOURCE


def _scan_sql(path: Path) -> tuple[str, int, list[tuple[int, str]], object]:
    """Read a stable SQL file once, hashing it while locating DDL line numbers."""
    for _ in range(3):
        before = path.stat()
        digest = hashlib.sha256()
        matches: list[tuple[int, str]] = []
        line_count = 0
        with path.open("rb") as stream:
            for line_count, raw_line in enumerate(stream, 1):
                digest.update(raw_line)
                line = raw_line.decode("utf-8", errors="replace")
                matches.extend((line_count, match.group(1)) for match in TABLE.finditer(line))
        after = path.stat()
        if before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns:
            return digest.hexdigest(), line_count, matches, after
    raise RuntimeError(f"SQL file changed repeatedly while indexing: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--root", type=Path, required=True, help="SQL file or directory")
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.exists() or not (args.root.is_dir() or args.root.is_file()):
        parser.error(f"SQL root is not a file or directory: {args.root}")
    if args.root.is_file() and args.root.suffix.lower() != ".sql":
        parser.error(f"SQL file must use the .sql extension: {args.root}")
    try:
        ensure_outside_source(args.workspace, args.root)
    except ValueError as exc:
        parser.error(str(exc))

    output = args.workspace / "indexes" / args.project / "table-index.jsonl"
    manifest = args.workspace / "indexes" / args.project / "table-manifest.json"
    try:
        source = load_isolated_source_index(args.workspace, args.project)
    except ValueError as exc:
        parser.error(str(exc))

    indexed_root = Path(source[0]["repository_root"]).resolve()
    workspace_root = args.workspace.resolve()
    sql_root = args.root.resolve()
    if not _inside(sql_root, indexed_root) and not _inside(sql_root, workspace_root):
        parser.error(f"external SQL root must be inside the analysis workspace: {workspace_root}")

    source_by_path = {
        Path(row.get("absolute_path", "")).resolve(strict=False): row
        for row in source
        if row.get("language") == "SQL"
    }
    candidates = [sql_root] if sql_root.is_file() else [
        path.resolve() for path in iter_source_files(sql_root) if path.suffix.lower() == ".sql"
    ]

    with exclusive_lock(output):
        old_by_key: dict[tuple[str, str], list[dict]] = {}
        for row in read_project_jsonl(output, args.project):
            old_by_key.setdefault((row["file"], _record_scope(row)), []).append(row)
        old_manifest = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
        old_hashes = old_manifest.get("file_hashes", {})
        old_stats = old_manifest.get("file_stats", {})

        rows: list[dict] = []
        parsed = reused = 0
        current_hashes: dict[str, str] = {}
        current_stats: dict[str, dict[str, int]] = {}
        current_paths: dict[str, str] = {}
        current_scopes: dict[str, str] = {}
        parsed_files: list[str] = []
        reused_files: list[str] = []
        for path in sorted(set(candidates)):
            if not path.is_file():
                continue
            source_row = source_by_path.get(path)
            if _inside(path, indexed_root):
                if source_row is None:
                    parser.error(f"SQL file inside project root is missing from source-index: {path}")
                scope = PROJECT_SOURCE
                relative = source_row["relative_path"]
                expected_digest = source_row["sha256"]
                expected_lines = source_row["line_count"]
                stat = path.stat()
            else:
                if not _inside(path, workspace_root):
                    parser.error(f"external SQL file escapes the analysis workspace: {path}")
                scope = EXTERNAL_SQL_SNAPSHOT
                relative = path.relative_to(workspace_root).as_posix()
                expected_digest = None
                expected_lines = None
                stat = path.stat()

            stats = {"size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            current_stats[relative] = stats
            current_paths[relative] = str(path)
            current_scopes[relative] = scope
            old_rows = old_by_key.get((relative, scope), [])
            if old_stats.get(relative) == stats and isinstance(old_hashes.get(relative), str) and old_rows:
                current_hashes[relative] = old_hashes[relative]
                for old_row in old_rows:
                    normalized = dict(old_row)
                    normalized["source_scope"] = scope
                    if scope == EXTERNAL_SQL_SNAPSHOT:
                        normalized["notes"] = [EXTERNAL_SQL_NOTE]
                    rows.append(normalized)
                reused += 1
                reused_files.append(relative)
                continue

            digest, line_count, definitions, stable_stat = _scan_sql(path)
            if expected_digest is not None and (digest != expected_digest or line_count != expected_lines):
                parser.error(f"SQL file no longer matches source-index; refresh source index first: {relative}")
            current_hashes[relative] = digest
            current_stats[relative] = {"size_bytes": stable_stat.st_size, "mtime_ns": stable_stat.st_mtime_ns}
            parsed += 1
            parsed_files.append(relative)
            for number, table in definitions:
                row = {
                    "project": args.project,
                    "table": table,
                    "file": relative,
                    "file_sha256": digest,
                    "start_line": number,
                    "end_line": number,
                    "columns": [],
                    "primary_key": [],
                    "unique_keys": [],
                    "indexes": [],
                    "classification": "FACT",
                    "confidence": "HIGH",
                    "source_scope": scope,
                }
                if scope == EXTERNAL_SQL_SNAPSHOT:
                    row["notes"] = [EXTERNAL_SQL_NOTE]
                rows.append(row)

        rows.sort(key=lambda row: (row["file"], row["start_line"], row["table"]))
        write_jsonl(output, rows)
        atomic_write(manifest, json.dumps({
            "project": args.project,
            "sql_root": str(sql_root),
            "file_hashes": current_hashes,
            "file_stats": current_stats,
            "file_paths": current_paths,
            "file_scopes": current_scopes,
            "content_read_files": sorted(parsed_files),
            "reused_without_content_read": sorted(reused_files),
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"SQL_TABLES_OK project={args.project} count={len(rows)} parsed={parsed} reused={reused} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
