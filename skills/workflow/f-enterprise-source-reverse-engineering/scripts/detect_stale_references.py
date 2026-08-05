#!/usr/bin/env python3
"""Report stale source evidence and impacted modules/documents."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, load_isolated_source_index, read_project_jsonl, sha256_file, atomic_write, locked_jsonl_update, validate_module_name, validate_source_snapshot

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", choices=("A", "B"), action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trust-source-index", action="store_true", help="reuse hashes from a source refresh that completed immediately before this command")
    parser.add_argument("--source-snapshot-id", help="required snapshot ID when --trust-source-index is used")
    args = parser.parse_args()
    stale = []
    projects = args.project or [
        project for project in ("A", "B")
        if (args.workspace / "indexes" / project / "source-index.jsonl").is_file()
    ]
    if not projects:
        parser.error("no Project A/B source index exists in the workspace")
    if args.trust_source_index and (len(projects) != 1 or not args.source_snapshot_id):
        parser.error("--trust-source-index requires one --project and --source-snapshot-id")
    affected_by_project = {
        project: {"interfaces": set(), "rules": set(), "modules": set()}
        for project in projects
    }
    for project in projects:
        affected_interfaces = affected_by_project[project]["interfaces"]
        affected_rules = affected_by_project[project]["rules"]
        affected_modules = affected_by_project[project]["modules"]
        try:
            rows = load_isolated_source_index(args.workspace, project)
            if args.trust_source_index:
                validate_source_snapshot(args.workspace, project, args.source_snapshot_id)
        except ValueError as exc:
            parser.error(str(exc))
        current = {}
        for row in rows:
            path = Path(row.get("absolute_path", ""))
            digest = row.get("sha256") if args.trust_source_index and path.is_file() else sha256_file(path) if path.is_file() else None
            current[row.get("relative_path")] = digest
            if row.get("sha256") != digest or row.get("analysis_status") == "STALE":
                labels = row.get("modules", [])
                affected_modules.update(item.get("module") for item in labels if isinstance(item, dict) and item.get("module"))
                stale.append({"project": project, "file": row.get("relative_path"), "indexed_sha256": row.get("previous_sha256") or row.get("sha256"), "current_sha256": digest, "modules": labels, "status": "STALE", "reason": "file deleted" if digest is None else "source index marked stale" if row.get("sha256") == digest else "file hash changed"})
        index_dir = args.workspace / "indexes" / project
        with exclusive_lock(index_dir / "derived-indexes"):
            for name in ("api-index.jsonl", "business-index.jsonl"):
                index_path = index_dir / name
                if not index_path.exists():
                    continue
                try:
                    read_project_jsonl(index_path, project)
                except ValueError as exc:
                    parser.error(str(exc))
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
                                try:
                                    validate_module_name(record["module"])
                                except ValueError as exc:
                                    parser.error(f"invalid affected module {record['module']!r}: {exc}")
                                affected_modules.add(record["module"])
                            if record.get("api_id"):
                                affected_interfaces.add(record["api_id"])
                            if record.get("type") == "business_rule" and record.get("business_id"):
                                affected_rules.add(record["business_id"])
                    return index_rows
                locked_jsonl_update(index_path, update)
            module_path = index_dir / "module-index.jsonl"
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
        for module in affected_by_project[project]["modules"]:
            try:
                validate_module_name(module)
            except ValueError as exc:
                parser.error(f"invalid affected module {module!r}: {exc}")
            documents.extend(str(path) for path in (args.workspace / "reverse-docs" / project_slug / "modules" / module).rglob("*.md"))
    affected_modules = set().union(*(values["modules"] for values in affected_by_project.values()))
    affected_interfaces = set().union(*(values["interfaces"] for values in affected_by_project.values()))
    affected_rules = set().union(*(values["rules"] for values in affected_by_project.values()))
    report = {"stale_evidence_count": len(stale), "affected_modules": sorted(affected_modules), "affected_interfaces": sorted(affected_interfaces), "affected_rules": sorted(affected_rules), "affected_by_project": {project: {key: sorted(value) for key, value in values.items()} for project, values in affected_by_project.items()}, "documents_requiring_review": sorted(documents), "items": stale}
    output = args.output or args.workspace / "reports" / "stale-references.json"
    atomic_write(output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"STALE_REPORT count={len(stale)} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
