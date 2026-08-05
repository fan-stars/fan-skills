#!/usr/bin/env python3
"""Build evidence-backed API and business indexes for one explicitly named module."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, load_isolated_source_index, read_project_jsonl, text_lines, validate_analysis_run_id, validate_module_name, write_jsonl

def evidence(project: str, symbol: dict, run_id: str, evidence_type: str = "implementation", start_line: int | None = None, end_line: int | None = None, semantic_basis: str = "indexed_symbol") -> dict:
    return {"project": project, "file": symbol["file"], "file_sha256": symbol["file_sha256"], "symbol": symbol["fully_qualified_name"], "start_line": start_line or symbol["start_line"], "end_line": end_line or symbol["end_line"], "evidence_type": evidence_type, "semantic_basis": semantic_basis, "confidence": "HIGH", "analysis_run_id": run_id, "status": "CURRENT"}

def route_evidence(project: str, route: dict, run_id: str) -> dict:
    return {"project": project, "file": route["file"], "file_sha256": route["file_sha256"], "symbol": "route declaration", "start_line": route["start_line"], "end_line": route["end_line"], "evidence_type": "route", "semantic_basis": "indexed_route_declaration", "confidence": "HIGH", "analysis_run_id": run_id, "status": "CURRENT"}


def coverage(status: str, rationale: str) -> dict:
    return {"status": status, "rationale": rationale}

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
        candidates = []
        for parameter_type in entry.get("parameter_types", []):
            candidate = class_by_name.get(parameter_type)
            rules = [item for item in symbols if candidate and item.get("container_symbol") == candidate["fully_qualified_name"] and item.get("name") == "rules"]
            if candidate and rules:
                validation.append(evidence(args.project, candidate, args.analysis_run_id, "validation", semantic_basis="controller_parameter_with_rules_method"))
                validation.extend(evidence(args.project, item, args.analysis_run_id, "validation", semantic_basis="validation_rules_method") for item in rules)
            elif candidate:
                candidates.append({"role": "validation", "symbol": candidate["fully_qualified_name"], "reason": "resolved controller parameter type lacks a rules method", "confidence": "MEDIUM"})
        controllers = [evidence(args.project, entry, args.analysis_run_id, "controller", semantic_basis="indexed_route_handler")]
        transactions = [evidence(args.project, item, args.analysis_run_id, "transaction", semantic_basis="detected_transaction_call") for item in visited if any("DB::transaction" in call for call in item.get("calls", []))]
        side_effects = [evidence(args.project, item, args.analysis_run_id, "side_effect", semantic_basis="detected_side_effect_call") for item in visited if any(token in " ".join(item.get("calls", [])) for token in ("::dispatch", "Event::", "Cache::", "Http::", "Queue::"))]
        persistence_symbols = []
        for item in visited:
            targets = [class_by_name.get(call.rpartition("::")[0]) for call in item.get("calls", [])]
            if item.get("tables") or any(target and target.get("tables") for target in targets):
                persistence_symbols.append(item)
            elif "Repository" in (item.get("container_symbol") or "") or "Model" in (item.get("namespace") or ""):
                candidates.append({"role": "persistence", "symbol": item["fully_qualified_name"], "reason": "name-only persistence candidate has no known table linkage", "confidence": "MEDIUM"})
        persistence = [evidence(args.project, item, args.analysis_run_id, "persistence", semantic_basis="reachable_symbol_links_known_table") for item in persistence_symbols]
        persistence_names = {item["fully_qualified_name"] for item in persistence_symbols}
        service_symbols = []
        for item in visited:
            calls = set(item.get("calls", []))
            calls_persistence = any(call in persistence_names for call in calls)
            has_orchestration = calls_persistence or any("DB::transaction" in call for call in calls) or any(token in " ".join(calls) for token in ("::dispatch", "Event::", "Cache::", "Http::", "Queue::"))
            if item is not entry and has_orchestration and item not in persistence_symbols:
                service_symbols.append(item)
            elif item is not entry and (item.get("container_symbol") or "").endswith("Service"):
                candidates.append({"role": "service", "symbol": item["fully_qualified_name"], "reason": "name-only service candidate lacks orchestration evidence", "confidence": "MEDIUM"})
        services = [evidence(args.project, item, args.analysis_run_id, "service", semantic_basis="reachable_orchestrator_calls_persistence_transaction_or_side_effect") for item in service_symbols]
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
        api = {"project": args.project, "module": args.module, "api_id": api_id, "method": route["method"], "path": route["path"], "classification": "FACT", "analysis_run_id": args.analysis_run_id, "evidence": [route_evidence(args.project, route, args.analysis_run_id)], "route_evidence": [route_evidence(args.project, route, args.analysis_run_id)], "controller_evidence": controllers, "validation_evidence": validation, "service_evidence": services, "persistence_evidence": persistence, "side_effect_evidence": side_effects, "transaction_evidence": transactions, "tables": related_tables, "coverage": {"validation": coverage("PRESENT" if validation else "UNRESOLVED", "validation rules are structurally linked" if validation else "no structurally verified validation rule"), "service": coverage("PRESENT" if services else "UNRESOLVED", "reachable orchestration symbol detected" if services else "no structurally verified orchestration symbol"), "persistence": coverage("PRESENT" if persistence else "UNRESOLVED", "reachable symbol links a known table" if persistence else "no structurally verified persistence link"), "transaction": coverage("PRESENT" if transactions else "UNRESOLVED", "transaction call detected" if transactions else "no transaction call detected; absence is not proof of non-applicability"), "side_effect": coverage("PRESENT" if side_effects else "UNRESOLVED", "side-effect call detected" if side_effects else "no side-effect call detected; absence is not proof of non-applicability"), "tables": coverage("PRESENT" if related_tables else "UNRESOLVED", "known table linkage detected" if related_tables else "no known table linkage")}, "candidates": candidates, "call_chain": [item["fully_qualified_name"] for item in visited], "status": "PARTIAL"}
        api_rows.append(api)
        business_rows.append({"project": args.project, "business_id": api_id, "type": "api", "module": args.module, "name": f"{route['method']} {route['path']}", "classification": "FACT", "confidence": "HIGH", "evidence": api["evidence"] + controllers + validation + services + persistence + side_effects, "related_apis": [api_id], "related_tables": related_tables, "analysis_run_id": args.analysis_run_id, "status": "PARTIAL"})
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
                    business_rows.append({"project": args.project, "business_id": rule_id, "type": "business_rule", "module": args.module, "name": f"status is set to {status_match.group(1)}", "classification": "FACT", "confidence": "HIGH", "evidence": [evidence(args.project, item, args.analysis_run_id, start_line=line_number, end_line=line_number, semantic_basis="literal_assignment_in_indexed_symbol")], "related_apis": [api_id], "related_tables": related_tables, "analysis_run_id": args.analysis_run_id, "status": "PARTIAL"})
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
