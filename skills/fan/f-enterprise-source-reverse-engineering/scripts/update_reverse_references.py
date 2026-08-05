#!/usr/bin/env python3
"""Rebuild simple referenced_by links from explicit references fields."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import locked_jsonl_update

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--index", type=Path, required=True); args = parser.parse_args()
    def update(rows):
        reverse = {r.get("relative_path"): [] for r in rows}
        for row in rows:
            for target in row.get("references", []):
                if target in reverse and row["relative_path"] not in reverse[target]: reverse[target].append(row["relative_path"])
        for row in rows: row["referenced_by"] = sorted(reverse[row["relative_path"]])
        return rows
    rows = locked_jsonl_update(args.index, update); print(f"REFERENCES_OK files={len(rows)}"); return 0
if __name__ == "__main__": raise SystemExit(main())
