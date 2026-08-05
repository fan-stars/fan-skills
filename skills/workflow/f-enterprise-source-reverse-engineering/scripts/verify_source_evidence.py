#!/usr/bin/env python3
"""Verify evidence objects against current files, hashes, paths and symbols."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import load_isolated_source_index, read_project_jsonl
from common.validation import validate_evidence

REQUIRED = {"project", "file", "file_sha256", "symbol", "start_line", "end_line", "evidence_type", "semantic_basis", "confidence", "analysis_run_id", "status"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.evidence.read_text(encoding="utf-8"))
    if isinstance(items, dict): items = [items]
    if not isinstance(items, list):
        parser.error("evidence document must be an object or an array of objects")
    errors = []
    loaded = {}
    fingerprint_caches = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"#{index}: evidence item must be an object")
            continue
        missing = REQUIRED - set(item)
        if missing: errors.append(f"#{index}: missing fields {sorted(missing)}"); continue
        if item["project"] not in ("A", "B"): errors.append(f"#{index}: project must be A or B"); continue
        project = item["project"]
        try:
            if project not in loaded:
                source = load_isolated_source_index(args.workspace, project)
                loaded[project] = (
                    {row["relative_path"]: row for row in source},
                    read_project_jsonl(args.workspace / "indexes" / project / "symbol-index.jsonl", project),
                    read_project_jsonl(args.workspace / "indexes" / project / "routes.jsonl", project),
                )
            source_by_file, symbols, routes = loaded[project]
            item_errors = validate_evidence(item, project, source_by_file, symbols, routes, fingerprint_cache=fingerprint_caches.setdefault(project, {}))
        except ValueError as exc:
            item_errors = [str(exc)]
        errors.extend(f"#{index}: {error}" for error in item_errors)
    if errors:
        print("EVIDENCE_INVALID")
        print("\n".join(errors))
        return 1
    print(f"EVIDENCE_OK count={len(items)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
