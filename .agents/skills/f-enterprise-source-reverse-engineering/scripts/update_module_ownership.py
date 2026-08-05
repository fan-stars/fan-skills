#!/usr/bin/env python3
"""Append module ownership labels; require opt-in before replacing an existing role."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import locked_jsonl_update, validate_module_name

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--role", choices=("PRIMARY", "SECONDARY", "SHARED", "INFRASTRUCTURE", "UNKNOWN"), required=True)
    parser.add_argument("--replace-role", action="store_true", help="replace the role for an existing file/module label")
    args = parser.parse_args()
    project = args.index.parent.name
    if project not in {"A", "B"}:
        parser.error("index must be indexes/A/source-index.jsonl or indexes/B/source-index.jsonl")
    try:
        validate_module_name(args.module)
    except ValueError as exc:
        parser.error(str(exc))
    def update(rows):
        found = False
        for row in rows:
            if row.get("project") != project:
                raise ValueError(f"project mismatch in source index: expected {project}")
            if row.get("relative_path") == args.file:
                labels = row.setdefault("modules", [])
                existing = next((item for item in labels if item.get("module") == args.module), None)
                if existing:
                    if existing.get("role") != args.role and not args.replace_role:
                        raise ValueError(
                            f"module {args.module} already has role {existing.get('role')}; "
                            "use --replace-role to change it"
                        )
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
