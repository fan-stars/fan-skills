"""Dependency-free integrity checks shared by gates and index validation."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .core import file_fingerprint, line_range_exists, read_jsonl, sha256_file


EVIDENCE_REQUIRED = {
    "project", "file", "file_sha256", "symbol", "start_line", "end_line",
    "evidence_type", "confidence", "analysis_run_id", "status",
}
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
CLASSIFICATION_VALUES = {"FACT", "INFERENCE", "UNRESOLVED", "CONFLICT", "RISK", "DEAD_CODE_CANDIDATE"}
SOURCE_REQUIRED = {
    "project", "repository_root", "relative_path", "absolute_path", "size_bytes",
    "mtime", "mtime_ns", "sha256", "line_count", "analysis_status", "modules",
}
INDEX_NAMES = (
    "source-index.jsonl", "symbol-index.jsonl", "module-index.jsonl",
    "routes.jsonl", "table-index.jsonl", "api-index.jsonl", "business-index.jsonl",
)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def evidence_fields(record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return every evidence object and structural errors without raising on bad input."""
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for key, value in record.items():
        if key != "evidence" and not key.endswith("_evidence"):
            continue
        if not isinstance(value, list):
            errors.append(f"{key} must be an array")
            continue
        for position, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{key}[{position}] must be an object")
            else:
                items.append(item)
    return items, errors


def validate_run_record(
    workspace: Path,
    project: str,
    run_id: str,
    module: str | None = None,
) -> list[str]:
    path = workspace / "analysis-runs" / project / f"{run_id}.json"
    if not path.is_file():
        return [f"analysis run is missing: {path}"]
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"analysis run is invalid JSON: {path}: {exc}"]
    if not isinstance(record, dict):
        return [f"analysis run must be an object: {path}"]
    errors = []
    required = {
        "analysis_run_id", "project", "requested_module", "started_at", "finished_at",
        "source_root", "workspace", "stages", "files_read", "files_written",
        "stale_evidence", "unresolved_questions", "final_status",
    }
    missing = sorted(required - set(record))
    if missing:
        errors.append(f"analysis run missing fields {missing}: {path}")
    if record.get("analysis_run_id") != run_id:
        errors.append(f"analysis run ID mismatch: {path}")
    if record.get("project") != project:
        errors.append(f"analysis run project mismatch: {path}")
    if module is not None and record.get("requested_module") != module:
        errors.append(f"analysis run module mismatch: {path}")
    stages = record.get("stages")
    if not isinstance(stages, list):
        errors.append(f"analysis run stages must be an array: {path}")
    else:
        if not stages:
            errors.append(f"analysis run stages must not be empty: {path}")
        for position, stage in enumerate(stages):
            if not isinstance(stage, dict) or not {"name", "command", "exit_code"} <= set(stage):
                errors.append(f"analysis run stage {position} is incomplete: {path}")
                continue
            if not isinstance(stage.get("command"), list) or not _integer(stage.get("exit_code")):
                errors.append(f"analysis run stage {position} has invalid types: {path}")
            elif stage["exit_code"] != 0 and not (stage.get("name") == "quality_gates" and stage["exit_code"] == 2):
                errors.append(f"analysis run stage {position} did not succeed: {path}")
    for key in ("files_read", "files_written", "stale_evidence", "unresolved_questions"):
        if key in record and not isinstance(record[key], list):
            errors.append(f"analysis run {key} must be an array: {path}")
    for key in ("requested_module", "started_at", "source_root", "workspace", "final_status"):
        if key in record and (not isinstance(record[key], str) or not record[key]):
            errors.append(f"analysis run {key} must be a non-empty string: {path}")
    if record.get("final_status") not in {"COMPLETED", "PARTIAL", "REVIEW_REQUIRED", "BLOCKED", "FAILED"}:
        errors.append(f"analysis run final_status is invalid: {path}")
    return errors


def validate_evidence(
    item: dict[str, Any],
    project: str,
    source_by_file: dict[str, dict[str, Any]],
    symbols: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    expected_run_id: str | None = None,
) -> list[str]:
    missing = sorted(EVIDENCE_REQUIRED - set(item))
    if missing:
        return [f"missing evidence fields {missing}"]
    errors = []
    if item.get("project") != project:
        errors.append("evidence project mismatch")
    if expected_run_id is not None and item.get("analysis_run_id") != expected_run_id:
        errors.append("evidence analysis_run_id mismatch")
    if item.get("status") != "CURRENT":
        errors.append("evidence is not CURRENT")
    if item.get("confidence") not in CONFIDENCE_VALUES:
        errors.append("evidence confidence is invalid")
    if not isinstance(item.get("evidence_type"), str) or not item["evidence_type"]:
        errors.append("evidence_type must be a non-empty string")
    relative = item.get("file")
    source = source_by_file.get(relative) if isinstance(relative, str) else None
    if source is None:
        errors.append(f"evidence file is not indexed: {relative}")
        return errors
    if source.get("analysis_status") == "STALE":
        errors.append(f"evidence source record is STALE: {relative}")
    path = Path(source.get("absolute_path", "")).resolve(strict=False)
    root = Path(source.get("repository_root", "")).resolve(strict=False)
    if not path.is_file() or not _inside(path, root):
        errors.append(f"evidence file is missing or outside root: {relative}")
        return errors
    actual_hash = sha256_file(path)
    if source.get("sha256") != actual_hash or item.get("file_sha256") != actual_hash:
        errors.append(f"evidence SHA-256 mismatch: {relative}")
    start = item.get("start_line")
    end = item.get("end_line")
    if not _integer(start) or not _integer(end) or not line_range_exists(path, start, end):
        errors.append(f"evidence line range is invalid: {relative}")
        return errors
    symbol_name = item.get("symbol")
    if symbol_name == "route declaration":
        matched = any(
            row.get("project") == project
            and row.get("file") == relative
            and row.get("file_sha256") == actual_hash
            and row.get("start_line") <= start <= end <= row.get("end_line")
            for row in routes
            if _integer(row.get("start_line")) and _integer(row.get("end_line"))
        )
    else:
        matched = any(
            row.get("project") == project
            and row.get("fully_qualified_name") == symbol_name
            and row.get("file") == relative
            and row.get("file_sha256") == actual_hash
            and row.get("start_line") <= start <= end <= row.get("end_line")
            for row in symbols
            if _integer(row.get("start_line")) and _integer(row.get("end_line"))
        )
    if not matched:
        errors.append(f"evidence symbol or route range is not indexed: {symbol_name}")
    return errors


def validate_project_indexes(workspace: Path, project: str) -> list[str]:
    """Validate one project without reading facts from the other project."""
    index_dir = workspace / "indexes" / project
    errors: list[str] = []
    indexes: dict[str, list[dict[str, Any]]] = {}
    for name in INDEX_NAMES:
        path = index_dir / name
        try:
            rows = read_jsonl(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            rows = []
        indexes[name] = rows
        if not rows:
            errors.append(f"{name}: missing or empty")

    source_rows = indexes["source-index.jsonl"]
    roots: set[Path] = set()
    source_by_file: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(source_rows):
        prefix = f"source-index.jsonl:{position}"
        missing = sorted(SOURCE_REQUIRED - set(row))
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
        if row.get("project") != project:
            errors.append(f"{prefix}: project mismatch")
        relative = row.get("relative_path")
        if not isinstance(relative, str) or not relative or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
            errors.append(f"{prefix}: invalid relative_path")
            continue
        if relative in source_by_file:
            errors.append(f"{prefix}: duplicate relative_path {relative}")
        source_by_file[relative] = row
        root = Path(row.get("repository_root", "")).resolve(strict=False)
        path = Path(row.get("absolute_path", "")).resolve(strict=False)
        roots.add(root)
        if path != (root / Path(*PurePosixPath(relative).parts)).resolve(strict=False) or not _inside(path, root):
            errors.append(f"{prefix}: absolute path does not match project root and relative path")
        if path.is_file():
            actual_hash, actual_lines, _ = file_fingerprint(path)
            if row.get("sha256") != actual_hash:
                errors.append(f"{prefix}: source SHA-256 mismatch")
            if not _integer(row.get("line_count")) or row.get("line_count") != actual_lines:
                errors.append(f"{prefix}: invalid line_count")
        elif row.get("analysis_status") != "STALE":
            errors.append(f"{prefix}: indexed source file is missing")
        modules = row.get("modules")
        if not isinstance(modules, list):
            errors.append(f"{prefix}: modules must be an array")
        else:
            for label_position, label in enumerate(modules):
                if not isinstance(label, dict) or not isinstance(label.get("module"), str) or not label.get("module") or label.get("role") not in {"PRIMARY", "SECONDARY", "SHARED", "INFRASTRUCTURE", "UNKNOWN"}:
                    errors.append(f"{prefix}: modules[{label_position}] is invalid")
    if len(roots) != 1:
        errors.append(f"source-index.jsonl: expected one repository_root, found {len(roots)}")

    symbols = indexes["symbol-index.jsonl"]
    for position, row in enumerate(symbols):
        prefix = f"symbol-index.jsonl:{position}"
        required = {"project", "symbol_id", "file", "file_sha256", "symbol_type", "name", "fully_qualified_name", "start_line", "end_line", "calls", "called_by"}
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
            continue
        source = source_by_file.get(row.get("file"))
        if row.get("project") != project or source is None:
            errors.append(f"{prefix}: project or source linkage mismatch")
            continue
        if row.get("file_sha256") != source.get("sha256"):
            errors.append(f"{prefix}: source hash linkage mismatch")
        if not _integer(row.get("start_line")) or not _integer(row.get("end_line")) or not 1 <= row["start_line"] <= row["end_line"] <= source.get("line_count", 0):
            errors.append(f"{prefix}: invalid line range")

    routes = indexes["routes.jsonl"]
    tables = indexes["table-index.jsonl"]
    for name, rows in (("routes.jsonl", routes), ("table-index.jsonl", tables)):
        for position, row in enumerate(rows):
            prefix = f"{name}:{position}"
            required = {"project", "file", "file_sha256", "start_line", "end_line", "classification", "confidence"}
            required.update({"method", "path"} if name == "routes.jsonl" else {"table"})
            missing = sorted(required - set(row))
            if missing:
                errors.append(f"{prefix}: missing fields {missing}")
            allowed_classifications = CLASSIFICATION_VALUES | ({"CANDIDATE"} if name == "routes.jsonl" else set())
            if row.get("classification") not in allowed_classifications:
                errors.append(f"{prefix}: invalid classification")
            if row.get("confidence") not in CONFIDENCE_VALUES:
                errors.append(f"{prefix}: invalid confidence")
            source = source_by_file.get(row.get("file"))
            if row.get("project") != project or source is None:
                errors.append(f"{prefix}: project or source linkage mismatch")
                continue
            if row.get("file_sha256") != source.get("sha256"):
                errors.append(f"{prefix}: source hash linkage mismatch")
            if not _integer(row.get("start_line")) or not _integer(row.get("end_line")) or not 1 <= row["start_line"] <= row["end_line"] <= source.get("line_count", 0):
                errors.append(f"{prefix}: invalid line range")

    modules = indexes["module-index.jsonl"]
    module_names = set()
    ownership_keys = ("primary_files", "secondary_files", "shared_files", "infrastructure_files", "unknown_files")
    for position, row in enumerate(modules):
        prefix = f"module-index.jsonl:{position}"
        module = row.get("module")
        if row.get("project") != project or not isinstance(module, str) or not module:
            errors.append(f"{prefix}: invalid project or module")
            continue
        required = {"status", "primary_files", "secondary_files", "shared_files", "quality_gates"}
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{prefix}: missing fields {missing}")
        if row.get("status") not in {"DISCOVERED", "PARTIAL", "ANALYZED", "REVIEW_REQUIRED", "BLOCKED"}:
            errors.append(f"{prefix}: invalid status")
        if module in module_names:
            errors.append(f"{prefix}: duplicate module {module}")
        module_names.add(module)
        for key in ownership_keys:
            values = row.get(key, [])
            if not isinstance(values, list):
                errors.append(f"{prefix}: {key} must be an array")
                continue
            for relative in values:
                if relative not in source_by_file:
                    errors.append(f"{prefix}: unknown owned file {relative}")

    known_tables = {row.get("table") for row in tables if isinstance(row.get("table"), str)}
    run_references: set[tuple[str, str | None]] = set()
    for name in ("api-index.jsonl", "business-index.jsonl"):
        for position, row in enumerate(indexes[name]):
            prefix = f"{name}:{position}"
            if row.get("project") != project:
                errors.append(f"{prefix}: project mismatch")
            module = row.get("module")
            if not isinstance(module, str) or not module:
                errors.append(f"{prefix}: missing module")
            run_id = row.get("analysis_run_id")
            if not isinstance(run_id, str) or not run_id:
                errors.append(f"{prefix}: missing analysis_run_id")
            else:
                run_references.add((run_id, module if isinstance(module, str) else None))
            evidence, structural = evidence_fields(row)
            errors.extend(f"{prefix}: {error}" for error in structural)
            for evidence_position, item in enumerate(evidence):
                item_errors = validate_evidence(item, project, source_by_file, symbols, routes, run_id if isinstance(run_id, str) else None)
                errors.extend(f"{prefix}:evidence:{evidence_position}: {error}" for error in item_errors)
            if name == "api-index.jsonl":
                required = {
                    "api_id", "method", "path", "route_evidence", "controller_evidence",
                    "validation_evidence", "service_evidence", "persistence_evidence",
                    "side_effect_evidence", "tables", "status",
                }
                missing = sorted(required - set(row))
                if missing:
                    errors.append(f"{prefix}: missing fields {missing}")
                for key in ("route_evidence", "controller_evidence", "validation_evidence", "service_evidence", "persistence_evidence", "side_effect_evidence"):
                    if not isinstance(row.get(key), list) or not row[key]:
                        errors.append(f"{prefix}: {key} must be a non-empty array")
                table_names = row.get("tables")
                if not isinstance(table_names, list):
                    errors.append(f"{prefix}: tables must be an array")
                else:
                    for table in table_names:
                        if table not in known_tables:
                            errors.append(f"{prefix}: unknown table {table}")
            else:
                required = {"business_id", "type", "name", "classification", "confidence", "evidence", "related_apis", "related_tables", "status"}
                missing = sorted(required - set(row))
                if missing:
                    errors.append(f"{prefix}: missing fields {missing}")
                if row.get("classification") not in CLASSIFICATION_VALUES:
                    errors.append(f"{prefix}: invalid classification")
                if row.get("confidence") not in CONFIDENCE_VALUES:
                    errors.append(f"{prefix}: invalid confidence")

    for run_id, module in sorted(run_references):
        errors.extend(validate_run_record(workspace, project, run_id, module))
    return errors


def matching_errors(errors: Iterable[str], *prefixes: str) -> list[str]:
    return [error for error in errors if error.startswith(prefixes)]
