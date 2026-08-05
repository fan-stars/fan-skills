#!/usr/bin/env python3
"""Build evidence-backed API and business indexes for one explicitly named module."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, load_isolated_source_index, read_project_jsonl, text_lines, validate_analysis_run_id, validate_module_name, write_jsonl

def evidence(project: str, symbol: dict, run_id: str, evidence_type: str = "implementation", start_line: int | None = None, end_line: int | None = None) -> dict:
    return {"project": project, "file": symbol["file"], "file_sha256": symbol["file_sha256"], "symbol": symbol["fully_qualified_name"], "start_line": start_line or symbol["start_line"], "end_line": end_line or symbol["end_line"], "evidence_type": evidence_type, "confidence": "HIGH", "analysis_run_id": run_id, "status": "CURRENT"}

def route_evidence(project: str, route: dict, run_id: str) -> dict:
    return {"project": project, "file": route["file"], "file_sha256": route["file_sha256"], "symbol": "route declaration", "start_line": route["start_line"], "end_line": route["end_line"], "evidence_type": "route", "confidence": "HIGH", "analysis_run_id": run_id, "status": "CURRENT"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--analysis-run-id", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_module_name(args.module)
        validate_analysis_run_id(args.analysis_run_id, args.project, args.module)
    except ValueError as exc:
        parser.error(str(exc))
    index_dir = args.workspace / "indexes" / args.project
    try:
        source = load_isolated_source_index(args.workspace, args.project)
        symbols = read_project_jsonl(index_dir / "symbol-index.jsonl", args.project)
        routes = read_project_jsonl(index_dir / "routes.jsonl", args.project)
        tables = read_project_jsonl(index_dir / "table-index.jsonl", args.project)
    except ValueError as exc:
        parser.error(str(exc))
    owned = {row["relative_path"] for row in source if any(isinstance(label, dict) and label.get("module") == args.module for label in row.get("modules", []))}
    if not owned:
        parser.error(f"module has no explicitly owned source files: {args.module}")
    by_name = {row["fully_qualified_name"]: row for row in symbols}
    class_by_short = {row["name"]: row for row in symbols if row.get("symbol_type") in {"class", "interface", "trait"}}
    class_by_name = {row["fully_qualified_name"]: row for row in symbols if row.get("symbol_type") in {"class", "interface", "trait"}}
    api_rows = []
    business_rows = []
    lines_by_file = {}
    for number, route in enumerate(routes, 1):
        entry_name = f"{route.get('controller')}::{route.get('action')}"
        entry = by_name.get(entry_name)
        if not entry or entry.get("file") not in owned:
            continue
        queue = [entry_name]
        visited: list[dict] = []
        while queue and len(visited) < 200:
            name = queue.pop(0)
            symbol = by_name.get(name)
            if not symbol or symbol in visited:
                continue
            visited.append(symbol)
            queue.extend(call for call in symbol.get("calls", []) if call in by_name)
        validation = []
        for parameter in entry.get("parameters", []):
            match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s+\$", parameter)
            candidate = class_by_short.get(match.group(1)) if match else None
            if candidate and candidate["name"].endswith("Request"):
                validation.append(evidence(args.project, candidate, args.analysis_run_id, "validation"))
                validation.extend(evidence(args.project, item, args.analysis_run_id, "validation") for item in symbols if item.get("container_symbol") == candidate["fully_qualified_name"] and item.get("name") == "rules")
        controllers = [evidence(args.project, entry, args.analysis_run_id, "controller")]
        services = [evidence(args.project, item, args.analysis_run_id, "service") for item in visited if (item.get("container_symbol") or "").endswith("Service")]
        persistence = [evidence(args.project, item, args.analysis_run_id, "persistence") for item in visited if ("Repository" in (item.get("container_symbol") or "") or "Model" in (item.get("namespace") or ""))]
        side_effects = [evidence(args.project, item, args.analysis_run_id, "side_effect") for item in visited if any(token in " ".join(item.get("calls", [])) for token in ("::dispatch", "Event::", "Cache::", "Http::", "Queue::"))]
        transactions = [evidence(args.project, item, args.analysis_run_id, "transaction") for item in visited if any("DB::transaction" in call for call in item.get("calls", []))]
        related_tables = set()
        for item in visited:
            related_tables.update(item.get("tables", []))
            for call in item.get("calls", []):
                target = class_by_name.get(call.rpartition("::")[0])
                if target:
                    related_tables.update(target.get("tables", []))
        known_tables = {row["table"] for row in tables}
        related_tables = sorted(related_tables & known_tables)
        api_id = f"{args.project}-{args.module.upper()}-API-{number:03d}"
        api = {"project": args.project, "module": args.module, "api_id": api_id, "method": route["method"], "path": route["path"], "classification": "FACT", "analysis_run_id": args.analysis_run_id, "evidence": [route_evidence(args.project, route, args.analysis_run_id)], "route_evidence": [route_evidence(args.project, route, args.analysis_run_id)], "controller_evidence": controllers, "validation_evidence": validation, "service_evidence": services, "persistence_evidence": persistence, "side_effect_evidence": side_effects, "transaction_evidence": transactions, "tables": related_tables, "call_chain": [item["fully_qualified_name"] for item in visited], "status": "PARTIAL"}
        required = (controllers, validation, services, persistence, side_effects)
        if all(required):
            api["status"] = "ANALYZED"
        api_rows.append(api)
        business_rows.append({"project": args.project, "business_id": api_id, "type": "api", "module": args.module, "name": f"{route['method']} {route['path']}", "classification": "FACT", "confidence": "HIGH", "evidence": api["evidence"] + controllers + validation + services + persistence + side_effects, "related_apis": [api_id], "related_tables": related_tables, "analysis_run_id": args.analysis_run_id, "status": api["status"]})
        for item in visited:
            path_row = next((row for row in source if row["relative_path"] == item["file"]), None)
            if not path_row:
                continue
            if item["file"] not in lines_by_file:
                lines_by_file[item["file"]] = text_lines(Path(path_row["absolute_path"]))
            lines = lines_by_file[item["file"]]
            for line_number in range(item["start_line"], min(item["end_line"], len(lines)) + 1):
                status_match = re.search(r"['\"]status['\"]\s*=>\s*['\"]([^'\"]+)['\"]", lines[line_number - 1])
                if status_match:
                    rule_id = f"{args.project}-{args.module.upper()}-RULE-{len([r for r in business_rows if r['type'] == 'business_rule']) + 1:03d}"
                    business_rows.append({"project": args.project, "business_id": rule_id, "type": "business_rule", "module": args.module, "name": f"status is set to {status_match.group(1)}", "classification": "FACT", "confidence": "HIGH", "evidence": [evidence(args.project, item, args.analysis_run_id, start_line=line_number, end_line=line_number)], "related_apis": [api_id], "related_tables": related_tables, "analysis_run_id": args.analysis_run_id, "status": "ANALYZED"})
    api_path = index_dir / "api-index.jsonl"
    business_path = index_dir / "business-index.jsonl"
    if not api_rows:
        parser.error(f"no evidence-backed API entry was found for module {args.module}; existing records were preserved")
    with exclusive_lock(index_dir / "derived-indexes"):
        api_rows = [row for row in read_project_jsonl(api_path, args.project) if row.get("module") != args.module] + api_rows
        business_rows = [row for row in read_project_jsonl(business_path, args.project) if row.get("module") != args.module] + business_rows
        api_rows.sort(key=lambda row: (row.get("module", ""), row.get("api_id", "")))
        business_rows.sort(key=lambda row: (row.get("module", ""), row.get("business_id", "")))
        write_jsonl(api_path, api_rows)
        write_jsonl(business_path, business_rows)
    print(f"BUSINESS_INDEX_OK project={args.project} module={args.module} module_apis={sum(row.get('module') == args.module for row in api_rows)} module_records={sum(row.get('module') == args.module for row in business_rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
