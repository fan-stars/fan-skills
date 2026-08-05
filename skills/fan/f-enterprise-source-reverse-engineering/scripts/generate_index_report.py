#!/usr/bin/env python3
"""Generate a compact human-readable report from isolated indexes."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import read_jsonl, atomic_write

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--workspace", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    sections = ["# Index Report", "", "| Project | Files | Stale |", "|---|---:|---:|"]
    for project in ("A", "B"):
        rows = read_jsonl(args.workspace / "indexes" / project / "source-index.jsonl")
        sections.append(f"| {project} | {len(rows)} | {sum(r.get('analysis_status') == 'STALE' for r in rows)} |")
    atomic_write(args.output, "\n".join(sections) + "\n"); print(f"REPORT_OK output={args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
