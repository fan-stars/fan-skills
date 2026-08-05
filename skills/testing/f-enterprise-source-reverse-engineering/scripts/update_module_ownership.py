#!/usr/bin/env python3
"""Append module ownership labels without overwriting existing labels."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import locked_jsonl_update

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--role", choices=("PRIMARY", "SECONDARY", "SHARED", "INFRASTRUCTURE", "UNKNOWN"), required=True)
    args = parser.parse_args()
    def update(rows):
        found = False
        for row in rows:
            if row.get("relative_path") == args.file:
                labels = row.setdefault("modules", [])
                existing = next((item for item in labels if item.get("module") == args.module), None)
                if existing:
                    existing["role"] = args.role
                else:
                    labels.append({"module": args.module, "role": args.role})
                found = True
        if not found:
            raise ValueError(f"file not found in index: {args.file}")
        return rows
    try: locked_jsonl_update(args.index, update)
    except ValueError as exc: parser.error(str(exc))
    print(f"OWNERSHIP_OK file={args.file} module={args.module} role={args.role}"); return 0
if __name__ == "__main__": raise SystemExit(main())
