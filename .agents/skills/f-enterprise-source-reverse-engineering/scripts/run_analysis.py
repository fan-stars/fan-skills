#!/usr/bin/env python3
"""Run the isolated index pipeline and persist a complete stage-by-stage run record."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, ensure_project_root_binding, exclusive_lock, file_fingerprint, iter_source_files, load_isolated_source_index, locked_jsonl_update, read_project_jsonl, validate_analysis_run_id, validate_module_name
from common.validation import REQUIRED_MODULE_DOCUMENTS, validate_run_record


def snapshot_outputs(workspace: Path, project: str) -> dict[str, int]:
    roots = (workspace / "indexes" / project, workspace / "reports" / project, workspace / "reports")
    snapshot = {}
    for root in roots:
        if root.exists():
            for path in root.glob("*"):
                if path.is_file():
                    snapshot[str(path.resolve())] = path.stat().st_mtime_ns
    return snapshot


def refresh_file_record(
    record: dict,
    root: Path,
    workspace: Path,
    project: str,
    module: str,
    before: dict[str, int],
    quality_gate_ran: bool = False,
) -> None:
    index_dir = workspace / "indexes" / project
    source_rows = load_isolated_source_index(workspace, project, root)
    scanned = {
        row["absolute_path"] for row in source_rows
        if isinstance(row.get("absolute_path"), str) and Path(row["absolute_path"]).is_file()
    }
    content_read = set()
    reused = set()
    for name in ("index-manifest.json", "symbol-manifest.json", "route-manifest.json", "table-manifest.json"):
        path = index_dir / name
        if not path.is_file():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        file_paths = manifest.get("file_paths", {})
        def recorded_path(relative: str) -> str:
            actual = file_paths.get(relative) if isinstance(file_paths, dict) else None
            return str(Path(actual).resolve(strict=False)) if isinstance(actual, str) else str((root / relative).resolve(strict=False))
        content_read.update(recorded_path(relative) for relative in manifest.get("content_read_files", []))
        reused.update(recorded_path(relative) for relative in manifest.get("reused_without_content_read", []))
        if name == "table-manifest.json" and isinstance(file_paths, dict):
            scanned.update(recorded_path(relative) for relative in file_paths)
            if quality_gate_ran:
                scopes = manifest.get("file_scopes", {})
                content_read.update(
                    recorded_path(relative) for relative, scope in scopes.items()
                    if scope == "EXTERNAL_SQL_SNAPSHOT"
                )
    record["files_scanned"] = sorted(set(record.get("files_scanned", [])) | scanned)
    api_path = index_dir / "api-index.jsonl"
    if api_path.exists():
        source_by_file = {row["relative_path"]: row["absolute_path"] for row in source_rows}
        symbol_files = {row["fully_qualified_name"]: row["file"] for row in read_project_jsonl(index_dir / "symbol-index.jsonl", project)}
        for api in read_project_jsonl(api_path, project):
            for symbol in api.get("call_chain", []):
                relative = symbol_files.get(symbol)
                if relative in source_by_file:
                    content_read.add(source_by_file[relative])
    project_slug = "project-a" if project == "A" else "project-b"
    document_root = workspace / "reverse-docs" / project_slug / "modules" / module
    context_files = {
        str((document_root / name).resolve())
        for name in REQUIRED_MODULE_DOCUMENTS
        if (document_root / name).is_file()
    }
    record["context_files_read"] = sorted(set(record.get("context_files_read", [])) | context_files)
    index_files = {str(path.resolve()) for path in index_dir.glob("*") if path.is_file()}
    record["files_read"] = sorted(set(record.get("files_read", [])) | content_read | index_files | context_files)
    record["files_reused_without_content_read"] = sorted(set(record.get("files_reused_without_content_read", [])) | (reused - content_read))
    after = snapshot_outputs(workspace, project)
    written = {path for path, mtime in after.items() if before.get(path) != mtime}
    written.add(str((workspace / "analysis-runs" / project / f"{record['analysis_run_id']}.json").resolve()))
    record["files_written"] = sorted(set(record.get("files_written", [])) | written)
    stale_path = workspace / "reports" / "stale-references.json"
    if stale_path.is_file():
        stale = json.loads(stale_path.read_text(encoding="utf-8"))
        record["stale_evidence"] = [item for item in stale.get("items", []) if item.get("project") == project]


def continuation_source_errors(workspace: Path, project: str, root: Path) -> list[str]:
    """Reject continuation when the source set or any indexed fingerprint changed."""
    indexed = {
        row["relative_path"]: row
        for row in load_isolated_source_index(workspace, project, root)
        if isinstance(row.get("relative_path"), str)
    }
    current = {path.relative_to(root).as_posix(): path for path in iter_source_files(root)}
    errors = []
    for relative in sorted(set(current) - set(indexed)):
        errors.append(f"new source file: {relative}")
    for relative, row in indexed.items():
        path = current.get(relative)
        if path is None:
            if row.get("analysis_status") != "STALE":
                errors.append(f"source file removed: {relative}")
            continue
        digest, lines, _ = file_fingerprint(path)
        if digest != row.get("sha256") or lines != row.get("line_count"):
            errors.append(f"source file changed: {relative}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--sql-root", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--analysis-run-id")
    continuation = parser.add_mutually_exclusive_group()
    continuation.add_argument("--resume", action="store_true", help="resume the first failed stage of an existing FAILED run")
    continuation.add_argument("--finalize", action="store_true", help="rerun only the gate for an enriched PARTIAL/REVIEW_REQUIRED run")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"repository root is not a directory: {root}")
    try:
        validate_module_name(args.module)
        ensure_project_root_binding(args.workspace, args.project, root)
    except ValueError as exc:
        parser.error(str(exc))
    started = datetime.now(timezone.utc)
    run_dir = args.workspace / "analysis-runs" / args.project
    outputs_before = snapshot_outputs(args.workspace, args.project)
    with exclusive_lock(run_dir / "run-ids"):
        if (args.resume or args.finalize) and not args.analysis_run_id:
            parser.error("--resume/--finalize requires --analysis-run-id")
        existing = []
        for path in run_dir.glob(f"{args.project}-{args.module}-{started:%Y%m%d}-*.json"):
            try:
                existing.append(int(path.stem.rpartition("-")[2]))
            except ValueError:
                continue
        sequence = max(existing, default=0) + 1
        run_id = args.analysis_run_id or f"{args.project}-{args.module}-{started:%Y%m%d}-{sequence:03d}"
        try:
            validate_analysis_run_id(run_id, args.project, args.module)
        except ValueError as exc:
            parser.error(str(exc))
        run_path = run_dir / f"{run_id}.json"
        if run_path.exists() and not (args.resume or args.finalize):
            parser.error(f"analysis run already exists; choose a new ID or use --resume/--finalize: {run_id}")
        if not run_path.exists() and (args.resume or args.finalize):
            parser.error(f"analysis run does not exist: {run_id}")
        run_path.parent.mkdir(parents=True, exist_ok=True)
        if not run_path.exists():
            run_path.touch(exist_ok=False)
    script_dir = Path(__file__).parent
    stages = [
        ("source_index", "build_source_index.py", ["--project", args.project, "--root", str(args.root), "--workspace", str(args.workspace)]),
        ("stale_references", "detect_stale_references.py", ["--project", args.project, "--workspace", str(args.workspace)]),
        ("symbol_index", "build_symbol_index.py", ["--project", args.project, "--workspace", str(args.workspace)]),
        ("routes", "extract_php_routes.py", ["--project", args.project, "--root", str(args.root), "--workspace", str(args.workspace)]),
        ("tables", "extract_sql_tables.py", ["--project", args.project, "--root", str(args.sql_root or args.root), "--workspace", str(args.workspace)]),
        ("modules", "build_module_index.py", ["--project", args.project, "--workspace", str(args.workspace)]),
        ("business", "build_business_index.py", ["--project", args.project, "--module", args.module, "--analysis-run-id", run_id, "--workspace", str(args.workspace)]),
    ]
    if args.resume or args.finalize:
        try:
            record = json.loads(run_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"cannot continue invalid run record: {exc}")
        if record.get("project") != args.project or record.get("requested_module") != args.module or Path(record.get("source_root", "")).resolve(strict=False) != root:
            parser.error("continuation arguments do not match the existing run")
        for key, default in (
            ("record_scope", "AUTOMATED_PIPELINE"), ("source_snapshot_id", None),
            ("resume_count", 0), ("resumed_at", []), ("context_files_read", []),
            ("finalization_count", 0), ("finalized_at", []), ("quality_gate_attempts", []),
            ("files_scanned", []), ("files_read", []),
            ("files_reused_without_content_read", []), ("files_written", []),
            ("stale_evidence", []), ("unresolved_questions", []),
        ):
            record.setdefault(key, default)
        if not isinstance(record.get("stages"), list):
            parser.error("existing analysis run stages must be an array")
        try:
            source_errors = continuation_source_errors(args.workspace, args.project, root)
        except ValueError as exc:
            parser.error(str(exc))
        if source_errors:
            parser.error("source changed since the recorded snapshot; create a new analysis run: " + "; ".join(source_errors[:5]))
        if args.resume:
            if record.get("final_status") != "FAILED":
                parser.error("only a FAILED analysis run can be resumed")
            successful = []
            for expected, stage in zip((item[0] for item in stages), record.get("stages", [])):
                if stage.get("name") != expected or stage.get("exit_code") != 0:
                    break
                successful.append(stage)
            record["stages"] = successful
            if not isinstance(record.get("resume_count"), int) or isinstance(record.get("resume_count"), bool):
                parser.error("existing analysis run resume_count is invalid")
            if not isinstance(record.get("resumed_at"), list):
                parser.error("existing analysis run resumed_at must be an array")
            record["resume_count"] += 1
            record["resumed_at"].append(started.isoformat())
        else:
            if record.get("final_status") not in {"PARTIAL", "REVIEW_REQUIRED"}:
                parser.error("only a PARTIAL or REVIEW_REQUIRED analysis run can be finalized")
            expected = [item[0] for item in stages] + ["quality_gates"]
            names = [stage.get("name") for stage in record["stages"] if isinstance(stage, dict)]
            if names != expected or any(stage.get("exit_code") != 0 for stage in record["stages"][:-1]) or record["stages"][-1].get("exit_code") != 2:
                parser.error("finalization requires one complete pipeline ending in a partial quality-gate result")
            if not isinstance(record.get("finalization_count"), int) or isinstance(record.get("finalization_count"), bool):
                parser.error("existing analysis run finalization_count is invalid")
            if not isinstance(record.get("finalized_at"), list) or not isinstance(record.get("quality_gate_attempts"), list):
                parser.error("existing analysis run finalization history is invalid")
            record["quality_gate_attempts"].append(record["stages"].pop())
            record["finalization_count"] += 1
            record["finalized_at"].append(started.isoformat())
        record["finished_at"] = None
        record["final_status"] = "RUNNING"
        record.pop("error", None)
        record.pop("recording_errors", None)
    else:
        record = {"analysis_run_id": run_id, "project": args.project, "requested_module": args.module, "started_at": started.isoformat(), "finished_at": None, "source_root": str(root), "workspace": str(args.workspace.resolve()), "record_scope": "AUTOMATED_PIPELINE", "source_snapshot_id": None, "resume_count": 0, "resumed_at": [], "finalization_count": 0, "finalized_at": [], "quality_gate_attempts": [], "stages": [], "files_scanned": [], "files_read": [], "context_files_read": [], "files_reused_without_content_read": [], "files_written": [], "stale_evidence": [], "unresolved_questions": [], "final_status": "RUNNING"}
    atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    report = None
    try:
        for name, script, arguments in stages[len(record["stages"]):]:
            if name == "stale_references":
                manifest = json.loads((args.workspace / "indexes" / args.project / "index-manifest.json").read_text(encoding="utf-8"))
                record["source_snapshot_id"] = manifest["snapshot_id"]
                arguments = [*arguments, "--trust-source-index", "--source-snapshot-id", manifest["snapshot_id"]]
            command = [sys.executable, str(script_dir / script), *arguments]
            before = time.monotonic()
            result = subprocess.run(command, capture_output=True, text=True)
            record["stages"].append({"name": name, "command": command, "exit_code": result.returncode, "duration_ms": round((time.monotonic() - before) * 1000), "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
            atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            if result.returncode:
                raise RuntimeError(f"stage {name} failed")
        manifest = json.loads((args.workspace / "indexes" / args.project / "index-manifest.json").read_text(encoding="utf-8"))
        record["source_snapshot_id"] = manifest["snapshot_id"]
        refresh_file_record(record, root, args.workspace, args.project, args.module, outputs_before)
        atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        gate_command = [sys.executable, str(script_dir / "evaluate_quality_gates.py"), "--project", args.project, "--module", args.module, "--analysis-run-id", run_id, "--workspace", str(args.workspace)]
        if not (args.resume or args.finalize):
            gate_command.extend(["--trust-source-index", "--source-snapshot-id", manifest["snapshot_id"]])
        before_gate = time.monotonic()
        gate = subprocess.run(gate_command, capture_output=True, text=True)
        record["stages"].append({"name": "quality_gates", "command": gate_command, "exit_code": gate.returncode, "duration_ms": round((time.monotonic() - before_gate) * 1000), "stdout": gate.stdout.strip(), "stderr": gate.stderr.strip()})
        if gate.returncode not in {0, 2}:
            raise RuntimeError(f"quality gate process failed with exit code {gate.returncode}: {gate.stderr.strip() or gate.stdout.strip()}")
        report_path = args.workspace / "reports" / args.project / f"{args.module}-quality-gates.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("project") != args.project or report.get("module") != args.module or report.get("analysis_run_id") != run_id:
            raise RuntimeError("quality gate report does not belong to this analysis run")
        if (gate.returncode == 0) != (report.get("status") == "ANALYZED"):
            raise RuntimeError("quality gate exit code and report status disagree")
        record["final_status"] = "COMPLETED" if report["status"] == "ANALYZED" else report["status"]
        record["unresolved_questions"] = [item["gate"] for item in report["gates"] if not item["passed"]]
    except Exception as exc:
        record["final_status"] = "FAILED"
        record["error"] = str(exc)
    try:
        quality_gate_ran = any(
            isinstance(stage, dict) and stage.get("name") == "quality_gates"
            for stage in record.get("stages", [])
        )
        refresh_file_record(
            record, root, args.workspace, args.project, args.module, outputs_before,
            quality_gate_ran,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        record.setdefault("recording_errors", []).append(str(exc))
        record["final_status"] = "FAILED"
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    final_errors = validate_run_record(args.workspace, args.project, run_id, args.module)
    if final_errors:
        record["final_status"] = "FAILED"
        record.setdefault("error", "final run record validation failed")
        record["recording_errors"] = sorted(set(record.get("recording_errors", []) + final_errors))
        atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    elif isinstance(report, dict) and report.get("status") == "ANALYZED":
        index_dir = args.workspace / "indexes" / args.project
        module_path = index_dir / "module-index.jsonl"
        def commit_analyzed(rows):
            for row in rows:
                if row.get("module") == args.module:
                    row["status"] = "ANALYZED"
                    row["last_analysis_run_id"] = run_id
            return rows
        def commit_records(rows):
            for row in rows:
                if row.get("module") == args.module and row.get("analysis_run_id") == run_id:
                    row["status"] = "ANALYZED"
            return rows
        with exclusive_lock(index_dir / "derived-indexes"):
            locked_jsonl_update(module_path, commit_analyzed)
            locked_jsonl_update(index_dir / "api-index.jsonl", commit_records)
            locked_jsonl_update(index_dir / "business-index.jsonl", commit_records)
            report["module_status_committed"] = "ANALYZED"
            report["commit_performed"] = True
            report["run_finalized"] = True
            atomic_write(args.workspace / "reports" / args.project / f"{args.module}-quality-gates.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"ANALYSIS_RUN status={record['final_status']} id={run_id} output={run_path}")
    return 0 if record["final_status"] in {"COMPLETED", "PARTIAL", "REVIEW_REQUIRED"} else 1

if __name__ == "__main__":
    raise SystemExit(main())
