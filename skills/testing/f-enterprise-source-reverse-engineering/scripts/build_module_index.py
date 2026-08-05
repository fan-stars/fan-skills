#!/usr/bin/env python3
"""Build a project-isolated module index from explicit source ownership labels."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, read_jsonl, write_jsonl

ROLES = {"PRIMARY": "primary_files", "SECONDARY": "secondary_files", "SHARED": "shared_files", "INFRASTRUCTURE": "infrastructure_files", "UNKNOWN": "unknown_files"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    index_dir = args.workspace / "indexes" / args.project
    source = read_jsonl(index_dir / "source-index.jsonl")
    if not source:
        parser.error("source index is missing or empty")
    modules: dict[str, dict] = {}
    for row in source:
        for label in row.get("modules", []):
            if not isinstance(label, dict) or not label.get("module"):
                continue
            module = label["module"]
            record = modules.setdefault(module, {"project": args.project, "module": module, "status": "PARTIAL", "primary_files": [], "secondary_files": [], "shared_files": [], "infrastructure_files": [], "unknown_files": [], "quality_gates": []})
            key = ROLES.get(label.get("role"), "unknown_files")
            if row["relative_path"] not in record[key]:
                record[key].append(row["relative_path"])
    rows = sorted(modules.values(), key=lambda item: item["module"])
    for row in rows:
        for key in ROLES.values():
            row[key].sort()
    output = index_dir / "module-index.jsonl"
    with exclusive_lock(output):
        write_jsonl(output, rows)
    print(f"MODULE_INDEX_OK project={args.project} modules={len(rows)} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
