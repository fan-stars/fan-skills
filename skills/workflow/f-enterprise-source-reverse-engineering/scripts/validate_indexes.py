#!/usr/bin/env python3
"""Validate index isolation and required record fields."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import read_jsonl

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", choices=("A", "B"), action="append")
    args = parser.parse_args()
    errors = []
    projects = args.project or ["A", "B"]
    roots = {}
    for project in projects:
        source = args.workspace / "indexes" / project / "source-index.jsonl"
        rows = read_jsonl(source)
        if not rows: errors.append(f"{project}: missing or empty {source}")
        for row in rows:
            for key in ("project", "relative_path", "absolute_path", "sha256", "line_count", "analysis_status", "modules"):
                if key not in row: errors.append(f"{project}:{row.get('relative_path')}: missing {key}")
            if row.get("project") != project: errors.append(f"{project}:{row.get('relative_path')}: project leakage")
            path = Path(row.get("absolute_path", "")).resolve(strict=False)
            root = Path(row.get("repository_root", "")).resolve(strict=False)
            roots[project] = root
            if path != root and root not in path.parents: errors.append(f"{project}:{row.get('relative_path')}: absolute path outside project root")
        for name in ("symbol-index.jsonl", "module-index.jsonl", "api-index.jsonl", "business-index.jsonl"):
            path = args.workspace / "indexes" / project / name
            rows = read_jsonl(path)
            if not rows: errors.append(f"{project}: missing or empty {path}")
            for row in rows:
                if row.get("project") != project: errors.append(f"{project}:{name}: project leakage")
    if len(roots) == 2 and roots.get("A") == roots.get("B"):
        errors.append("A/B repository roots must be distinct")
    if errors:
        print("INDEX_INVALID\n" + "\n".join(errors)); return 1
    print("INDEXES_OK projects=A,B"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
