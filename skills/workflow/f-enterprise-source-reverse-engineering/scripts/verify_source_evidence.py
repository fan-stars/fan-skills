#!/usr/bin/env python3
"""Verify evidence objects against current files, hashes, paths and symbols."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import line_range_exists, read_jsonl, sha256_file

REQUIRED = {"project", "file", "file_sha256", "symbol", "start_line", "end_line", "evidence_type", "confidence", "analysis_run_id"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.evidence.read_text(encoding="utf-8"))
    if isinstance(items, dict): items = [items]
    errors = []
    symbols = {row["project"]: read_jsonl(args.workspace / "indexes" / row["project"] / "symbol-index.jsonl") for row in ({"project": "A"}, {"project": "B"})}
    for index, item in enumerate(items):
        missing = REQUIRED - set(item)
        if missing: errors.append(f"#{index}: missing fields {sorted(missing)}"); continue
        if item["project"] not in ("A", "B"): errors.append(f"#{index}: project must be A or B"); continue
        rows = read_jsonl(args.workspace / "indexes" / item["project"] / "source-index.jsonl")
        row = next((x for x in rows if x.get("relative_path") == item["file"]), None)
        if not row: errors.append(f"#{index}: file is outside indexed project: {item['file']}"); continue
        if row.get("project") != item["project"]:
            errors.append(f"#{index}: project leakage in source index: {item['file']}"); continue
        path = Path(row["absolute_path"])
        root = Path(row["repository_root"]).resolve()
        if not path.is_file() or (path.resolve() != root and root not in path.resolve().parents):
            errors.append(f"#{index}: file missing or outside project root: {item['file']}"); continue
        if sha256_file(path) != item["file_sha256"]: errors.append(f"#{index}: SHA-256 mismatch: {item['file']}")
        if not line_range_exists(path, int(item["start_line"]), int(item["end_line"])): errors.append(f"#{index}: invalid line range: {item['file']}")
        symbol = item["symbol"]
        if symbol and symbol != "route declaration" and not any(s.get("project") == item["project"] and (s.get("fully_qualified_name") == symbol or s.get("name") == symbol) and s.get("file") == item["file"] and int(s.get("start_line", 0)) <= int(item["start_line"]) <= int(s.get("end_line", 0)) for s in symbols[item["project"]]):
            errors.append(f"#{index}: symbol not found in evidence range: {symbol}")
    if errors:
        print("EVIDENCE_INVALID")
        print("\n".join(errors))
        return 1
    print(f"EVIDENCE_OK count={len(items)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
