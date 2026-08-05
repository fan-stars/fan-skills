#!/usr/bin/env python3
"""Query file ownership, reverse callers, or business-rule API/table links."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import read_jsonl

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file")
    group.add_argument("--callers-of")
    group.add_argument("--business-rule")
    args = parser.parse_args()
    root = args.workspace / "indexes" / args.project
    if args.file:
        rows = [row for row in read_jsonl(root / "source-index.jsonl") if row.get("relative_path") == args.file]
        result = [{"project": args.project, "file": row["relative_path"], "modules": row.get("modules", [])} for row in rows]
    elif args.callers_of:
        rows = [row for row in read_jsonl(root / "symbol-index.jsonl") if row.get("fully_qualified_name") == args.callers_of or row.get("name") == args.callers_of]
        result = [{"project": args.project, "symbol": row["fully_qualified_name"], "called_by": row.get("called_by", [])} for row in rows]
    else:
        needle = args.business_rule.lower()
        rows = [row for row in read_jsonl(root / "business-index.jsonl") if row.get("type") == "business_rule" and (needle in row.get("business_id", "").lower() or needle in row.get("name", "").lower())]
        result = [{"project": args.project, "business_id": row["business_id"], "name": row.get("name"), "related_apis": row.get("related_apis", []), "related_tables": row.get("related_tables", []), "evidence": row.get("evidence", [])} for row in rows]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result else 1

if __name__ == "__main__":
    raise SystemExit(main())
