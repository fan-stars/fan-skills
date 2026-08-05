#!/usr/bin/env python3
"""Validate index isolation and required record fields."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import read_jsonl
from common.validation import validate_project_indexes

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", choices=("A", "B"), action="append")
    parser.add_argument("--trust-source-index", action="store_true")
    parser.add_argument("--source-snapshot-id")
    args = parser.parse_args()
    projects = list(dict.fromkeys(args.project or ["A", "B"]))
    if args.trust_source_index and (len(projects) != 1 or not args.source_snapshot_id):
        parser.error("--trust-source-index requires one --project and --source-snapshot-id")
    if args.source_snapshot_id and not args.trust_source_index:
        parser.error("--source-snapshot-id requires --trust-source-index")
    errors = []
    for project in projects:
        errors.extend(f"{project}: {error}" for error in validate_project_indexes(
            args.workspace, project,
            trust_source_index=args.trust_source_index,
            source_snapshot_id=args.source_snapshot_id,
        ))
    if len(projects) == 2:
        roots = []
        for project in projects:
            source = args.workspace / "indexes" / project / "source-index.jsonl"
            try:
                first = read_jsonl(source)[0]
                roots.append(Path(first["repository_root"]).resolve(strict=False))
            except (IndexError, KeyError, OSError, ValueError):
                pass
        if len(roots) == 2 and roots[0] == roots[1]:
            errors.append("A/B repository roots must be distinct")
    if errors:
        print("INDEX_INVALID\n" + "\n".join(errors)); return 1
    print(f"INDEXES_OK projects={','.join(projects)}"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
