#!/usr/bin/env python3
"""Report stale source evidence and impacted modules/documents."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import read_jsonl, sha256_file, atomic_write, locked_jsonl_update

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", choices=("A", "B"), action="append")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    stale = []
    affected_interfaces = set()
    affected_rules = set()
    affected_modules = set()
    projects = args.project or ["A", "B"]
    for project in projects:
        rows = read_jsonl(args.workspace / "indexes" / project / "source-index.jsonl")
        current = {}
        for row in rows:
            path = Path(row.get("absolute_path", ""))
            digest = sha256_file(path) if path.is_file() else None
            current[row.get("relative_path")] = digest
            if row.get("sha256") != digest:
                labels = row.get("modules", [])
                affected_modules.update(item.get("module") for item in labels if isinstance(item, dict) and item.get("module"))
                stale.append({"project": project, "file": row.get("relative_path"), "indexed_sha256": row.get("sha256"), "current_sha256": digest, "modules": labels, "status": "STALE", "reason": "file hash changed" if digest else "file deleted"})
        for name in ("api-index.jsonl", "business-index.jsonl"):
            index_path = args.workspace / "indexes" / project / name
            if not index_path.exists():
                continue
            def update(index_rows):
                for record in index_rows:
                    record_stale = False
                    for key, values in record.items():
                        if key != "evidence" and not key.endswith("_evidence"):
                            continue
                        if not isinstance(values, list):
                            continue
                        for item in values:
                            if not isinstance(item, dict) or item.get("project") != project:
                                continue
                            digest = current.get(item.get("file"))
                            if digest != item.get("file_sha256"):
                                item["status"] = "STALE"
                                record_stale = True
                    if record_stale:
                        record["status"] = "REVIEW_REQUIRED"
                        if record.get("module"):
                            affected_modules.add(record["module"])
                        if record.get("api_id"):
                            affected_interfaces.add(record["api_id"])
                        if record.get("type") == "business_rule":
                            affected_rules.add(record.get("business_id"))
                return index_rows
            locked_jsonl_update(index_path, update)
        module_path = args.workspace / "indexes" / project / "module-index.jsonl"
        if module_path.exists():
            def update_modules(module_rows):
                for module in module_rows:
                    if module.get("module") in affected_modules:
                        module["status"] = "REVIEW_REQUIRED"
                return module_rows
            locked_jsonl_update(module_path, update_modules)
    documents = []
    for project in projects:
        project_slug = "project-a" if project == "A" else "project-b"
        for module in affected_modules:
            documents.extend(str(path) for path in (args.workspace / "reverse-docs" / project_slug / "modules" / module).rglob("*.md"))
    report = {"stale_evidence_count": len(stale), "affected_modules": sorted(affected_modules), "affected_interfaces": sorted(affected_interfaces), "affected_rules": sorted(affected_rules), "documents_requiring_review": sorted(documents), "items": stale}
    output = args.output or args.workspace / "reports" / "stale-references.json"
    atomic_write(output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"STALE_REPORT count={len(stale)} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
