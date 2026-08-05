#!/usr/bin/env python3
"""Print a stable numbered excerpt; never writes to the analyzed repository."""
from __future__ import annotations
import argparse
from pathlib import Path
from common.core import text_lines

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    lines = text_lines(args.file)
    end = args.end or len(lines)
    if not 1 <= args.start <= end <= len(lines):
        parser.error("line range is outside the file")
    for number in range(args.start, end + 1):
        print(f"{number:>6}\t{lines[number - 1]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
