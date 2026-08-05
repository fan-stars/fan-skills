#!/usr/bin/env python3
"""Build a project-isolated module index from explicit source ownership labels."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, load_isolated_source_index, read_project_jsonl, validate_module_name, write_jsonl

ROLES = {"PRIMARY": "primary_files", "SECONDARY": "secondary_files", "SHARED": "shared_files", "INFRASTRUCTURE": "infrastructure_files", "UNKNOWN": "unknown_files"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    index_dir = args.workspace / "indexes" / args.project
    try:
        source = load_isolated_source_index(args.workspace, args.project)
    except ValueError as exc:
        parser.error(str(exc))
    output = index_dir / "module-index.jsonl"
    old_modules = {row.get("module"): row for row in read_project_jsonl(output, args.project)}
    modules: dict[str, dict] = {}
    for row in source:
        for label in row.get("modules", []):
            if not isinstance(label, dict) or not label.get("module"):
                continue
            module = label["module"]
            try:
                validate_module_name(module)
            except ValueError as exc:
                parser.error(f"invalid module label {module!r}: {exc}")
            record = modules.setdefault(module, {"project": args.project, "module": module, "status": "PARTIAL", "primary_files": [], "secondary_files": [], "shared_files": [], "infrastructure_files": [], "unknown_files": [], "quality_gates": []})
            key = ROLES.get(label.get("role"), "unknown_files")
            if row["relative_path"] not in record[key]:
                record[key].append(row["relative_path"])
    rows = sorted(modules.values(), key=lambda item: item["module"])
    for row in rows:
        for key in ROLES.values():
            row[key].sort()
        old = old_modules.get(row["module"])
        if old:
            ownership_changed = any(old.get(key, []) != row.get(key, []) for key in ROLES.values())
            row["status"] = "REVIEW_REQUIRED" if ownership_changed and old.get("status") == "ANALYZED" else old.get("status", "PARTIAL")
            row["quality_gates"] = [] if ownership_changed else old.get("quality_gates", [])
    with exclusive_lock(index_dir / "derived-indexes"):
        write_jsonl(output, rows)
    print(f"MODULE_INDEX_OK project={args.project} modules={len(rows)} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
