#!/usr/bin/env python3
"""Validate required module documents, evidence labels and unresolved placeholders."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common.validation import validate_module_documents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--module", required=True)
    args = parser.parse_args()
    errors = validate_module_documents(args.workspace, args.project, args.module)
    if errors:
        print("DOCUMENTS_INVALID\n" + "\n".join(errors))
        return 1
    print(f"DOCUMENTS_OK project={args.project} module={args.module}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
