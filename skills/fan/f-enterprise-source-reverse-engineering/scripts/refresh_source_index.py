#!/usr/bin/env python3
"""Incrementally refresh one source index and propagate changed evidence to STALE."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--verify-all", action="store_true")
    args = parser.parse_args()
    script_dir = Path(__file__).parent
    build_command = [
        sys.executable, str(script_dir / "build_source_index.py"),
        "--project", args.project, "--root", str(args.root), "--workspace", str(args.workspace),
    ]
    if args.verify_all:
        build_command.append("--verify-all")
    build = subprocess.run(build_command)
    if build.returncode:
        return build.returncode
    stale = subprocess.run([
        sys.executable, str(script_dir / "detect_stale_references.py"),
        "--workspace", str(args.workspace), "--project", args.project, "--trust-source-index",
    ])
    return stale.returncode


if __name__ == "__main__":
    raise SystemExit(main())
