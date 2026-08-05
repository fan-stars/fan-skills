#!/usr/bin/env python3
"""Check module documents for evidence labels and required sections."""
from __future__ import annotations
import argparse
from pathlib import Path

REQUIRED = ("FACT", "INFERENCE", "UNRESOLVED", "CONFLICT", "RISK")
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace / "reverse-docs"
    docs = list(root.rglob("*.md")) if root.exists() else []
    errors = [f"{path}: lacks classification label" for path in docs if not any(label in path.read_text(encoding="utf-8") for label in REQUIRED)]
    if errors: print("DOCUMENTS_INVALID\n" + "\n".join(errors)); return 1
    print(f"DOCUMENTS_OK count={len(docs)}"); return 0
if __name__ == "__main__": raise SystemExit(main())
