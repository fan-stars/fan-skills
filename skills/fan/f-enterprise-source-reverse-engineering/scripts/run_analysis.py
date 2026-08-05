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
from common.core import atomic_write, read_jsonl

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--sql-root", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--analysis-run-id")
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    run_dir = args.workspace / "analysis-runs" / args.project
    existing = len(list(run_dir.glob(f"{args.project}-{args.module}-{started:%Y%m%d}-*.json"))) + 1
    run_id = args.analysis_run_id or f"{args.project}-{args.module}-{started:%Y%m%d}-{existing:03d}"
    run_path = run_dir / f"{run_id}.json"
    if run_path.exists():
        parser.error(f"analysis run already exists; choose a new ID: {run_id}")
    script_dir = Path(__file__).parent
    stages = [
        ("source_index", "build_source_index.py", ["--project", args.project, "--root", str(args.root), "--workspace", str(args.workspace)]),
        ("symbol_index", "build_symbol_index.py", ["--project", args.project, "--workspace", str(args.workspace)]),
        ("routes", "extract_php_routes.py", ["--project", args.project, "--root", str(args.root), "--workspace", str(args.workspace)]),
        ("tables", "extract_sql_tables.py", ["--project", args.project, "--root", str(args.sql_root or args.root), "--workspace", str(args.workspace)]),
        ("modules", "build_module_index.py", ["--project", args.project, "--workspace", str(args.workspace)]),
        ("business", "build_business_index.py", ["--project", args.project, "--module", args.module, "--analysis-run-id", run_id, "--workspace", str(args.workspace)]),
    ]
    record = {"analysis_run_id": run_id, "project": args.project, "requested_module": args.module, "started_at": started.isoformat(), "finished_at": None, "source_root": str(args.root.resolve()), "workspace": str(args.workspace.resolve()), "stages": [], "files_scanned": [], "files_read": [], "files_reused_without_content_read": [], "files_written": [], "stale_evidence": [], "unresolved_questions": [], "final_status": "FAILED"}
    atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    try:
        for name, script, arguments in stages:
            command = [sys.executable, str(script_dir / script), *arguments]
            before = time.monotonic()
            result = subprocess.run(command, capture_output=True, text=True)
            record["stages"].append({"name": name, "command": command, "exit_code": result.returncode, "duration_ms": round((time.monotonic() - before) * 1000), "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
            atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            if result.returncode:
                raise RuntimeError(f"stage {name} failed")
        gate_command = [sys.executable, str(script_dir / "evaluate_quality_gates.py"), "--project", args.project, "--module", args.module, "--analysis-run-id", run_id, "--workspace", str(args.workspace)]
        gate = subprocess.run(gate_command, capture_output=True, text=True)
        record["stages"].append({"name": "quality_gates", "command": gate_command, "exit_code": gate.returncode, "stdout": gate.stdout.strip(), "stderr": gate.stderr.strip()})
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
        record["error"] = str(exc)
    index_dir = args.workspace / "indexes" / args.project
    source_manifest = json.loads((index_dir / "index-manifest.json").read_text(encoding="utf-8")) if (index_dir / "index-manifest.json").exists() else {}
    record["files_scanned"] = sorted(str(path) for path in args.root.rglob("*") if path.is_file())
    record["files_reused_without_content_read"] = [str(args.root / relative) for relative in source_manifest.get("reused_without_content_read", [])]
    content_read = {str(args.root / relative) for relative in source_manifest.get("content_read_files", [])}
    api_path = index_dir / "api-index.jsonl"
    if api_path.exists():
        source_rows = {row["relative_path"]: row["absolute_path"] for row in read_jsonl(index_dir / "source-index.jsonl")}
        symbol_rows = {row["fully_qualified_name"]: row["file"] for row in read_jsonl(index_dir / "symbol-index.jsonl")}
        for api in read_jsonl(api_path):
            for symbol in api.get("call_chain", []):
                if symbol in symbol_rows and symbol_rows[symbol] in source_rows:
                    content_read.add(source_rows[symbol_rows[symbol]])
    record["files_read"] = sorted(content_read | {str(path) for path in index_dir.glob("*.jsonl") if path.is_file()})
    record["files_written"] = sorted(str(path) for path in list(index_dir.glob("*")) + list((args.workspace / "reports" / args.project).glob("*")) if path.is_file())
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(run_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"ANALYSIS_RUN status={record['final_status']} id={run_id} output={run_path}")
    return 0 if record["final_status"] in {"COMPLETED", "PARTIAL", "REVIEW_REQUIRED"} else 1

if __name__ == "__main__":
    raise SystemExit(main())
