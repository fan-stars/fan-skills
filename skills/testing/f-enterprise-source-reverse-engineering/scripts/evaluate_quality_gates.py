#!/usr/bin/env python3
"""Evaluate 18 executable gates and prevent incomplete modules becoming ANALYZED."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, exclusive_lock, load_isolated_source_index, locked_jsonl_update, read_project_jsonl, validate_analysis_run_id, validate_module_name
from common.validation import (
    EVIDENCE_TYPES,
    evidence_fields,
    matching_errors,
    validate_evidence,
    validate_module_documents,
    validate_project_indexes,
    validate_run_record,
)

GATE_NAMES = (
    "source_index", "symbol_index", "business_index", "module_ownership", "route_evidence", "controller_evidence",
    "validation_evidence", "service_evidence", "persistence_evidence", "table_evidence", "business_rules",
    "state_transitions", "transactions", "concurrency_or_idempotency", "side_effects", "cross_module_dependencies",
    "current_evidence", "analysis_run_record",
)

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
    root = args.workspace / "indexes" / args.project
    source_load_error = None
    try:
        source = load_isolated_source_index(args.workspace, args.project)
        symbols = read_project_jsonl(root / "symbol-index.jsonl", args.project)
        business_all = read_project_jsonl(root / "business-index.jsonl", args.project)
        apis_all = read_project_jsonl(root / "api-index.jsonl", args.project)
        modules = read_project_jsonl(root / "module-index.jsonl", args.project)
        routes = read_project_jsonl(root / "routes.jsonl", args.project)
        tables = read_project_jsonl(root / "table-index.jsonl", args.project)
    except ValueError as exc:
        source = []
        symbols = []
        business_all = []
        apis_all = []
        modules = []
        routes = []
        tables = []
        source_load_error = str(exc)
    business = [row for row in business_all if row.get("module") == args.module]
    apis = [row for row in apis_all if row.get("module") == args.module]
    module = next((row for row in modules if row.get("module") == args.module), None)
    project_errors = validate_project_indexes(args.workspace, args.project, args.module, allow_in_progress_runs=True)
    if source_load_error:
        project_errors.append(f"source-index.jsonl: {source_load_error}")
    source_by_file = {row.get("relative_path"): row for row in source if isinstance(row.get("relative_path"), str)}
    evidence = []
    evidence_errors = []
    fingerprint_cache = {}
    for row_number, row in enumerate(business + apis):
        items, structural_errors = evidence_fields(row)
        evidence.extend(items)
        evidence_errors.extend(f"record {row_number}: {error}" for error in structural_errors)
        for item_number, item in enumerate(items):
            errors = validate_evidence(item, args.project, source_by_file, symbols, routes, args.analysis_run_id, fingerprint_cache)
            evidence_errors.extend(f"record {row_number} evidence {item_number}: {error}" for error in errors)
    symbols_by_name = {row.get("fully_qualified_name"): row for row in symbols}
    api_link_errors = []
    for api in apis:
        route = next((
            row for row in routes
            if row.get("method") == api.get("method") and row.get("path") == api.get("path")
            and any(
                item.get("file") == row.get("file")
                and item.get("file_sha256") == row.get("file_sha256")
                and item.get("start_line") == row.get("start_line")
                and item.get("end_line") == row.get("end_line")
                for item in api.get("route_evidence", []) if isinstance(item, dict)
            )
        ), None)
        if route is None:
            api_link_errors.append(f"API {api.get('api_id')}: route evidence does not match method/path")
            continue
        controller_name = f"{route.get('controller')}::{route.get('action')}"
        controller = symbols_by_name.get(controller_name)
        if controller is None or not any(item.get("symbol") == controller_name for item in api.get("controller_evidence", []) if isinstance(item, dict)):
            api_link_errors.append(f"API {api.get('api_id')}: controller evidence does not match route handler")
            continue
        reachable = set()
        queue = [controller_name]
        while queue and len(reachable) < 10000:
            name = queue.pop(0)
            if name in reachable or name not in symbols_by_name:
                continue
            reachable.add(name)
            queue.extend(call for call in symbols_by_name[name].get("calls", []) if call in symbols_by_name)
        for key in ("controller_evidence", "service_evidence", "persistence_evidence", "transaction_evidence", "side_effect_evidence"):
            for item in api.get(key, []):
                if isinstance(item, dict) and item.get("symbol") not in reachable:
                    api_link_errors.append(f"API {api.get('api_id')}: {key} symbol is not reachable from controller")
        for item in api.get("transaction_evidence", []):
            symbol = symbols_by_name.get(item.get("symbol")) if isinstance(item, dict) else None
            if symbol is not None and not any("DB::transaction" in call for call in symbol.get("calls", [])):
                api_link_errors.append(f"API {api.get('api_id')}: transaction evidence has no transaction call")
        for item in api.get("side_effect_evidence", []):
            symbol = symbols_by_name.get(item.get("symbol")) if isinstance(item, dict) else None
            calls = " ".join(symbol.get("calls", [])) if symbol else ""
            if symbol is not None and not any(token in calls for token in ("::dispatch", "Event::", "Cache::", "Http::", "Queue::")):
                api_link_errors.append(f"API {api.get('api_id')}: side-effect evidence has no detected side-effect call")
    evidence_errors.extend(api_link_errors)
    run_errors = validate_run_record(args.workspace, args.project, args.analysis_run_id, args.module, allow_in_progress=True)
    document_errors = validate_module_documents(args.workspace, args.project, args.module)
    table_names = {row.get("table") for row in tables if row.get("project") == args.project}
    module_files = set(module.get("primary_files", [])) if isinstance(module, dict) and isinstance(module.get("primary_files"), list) else set()
    module_ownership_valid = bool(module_files) and all(
        relative in source_by_file
        and any(
            isinstance(label, dict) and label.get("module") == args.module and label.get("role") == "PRIMARY"
            for label in source_by_file[relative].get("modules", [])
        )
        for relative in module_files
    )
    def evidence_group_valid(key: str) -> bool:
        expected = EVIDENCE_TYPES[key]
        return bool(apis) and all(
            isinstance(row.get(key), list)
            and row[key]
            and all(isinstance(item, dict) and item.get("evidence_type") == expected for item in row[key])
            for row in apis
        ) and not evidence_errors
    has_type = lambda kind: any(row.get("type") == kind and isinstance(row.get("evidence"), list) and row["evidence"] for row in business)
    checks = {
        "source_index": bool(source) and not matching_errors(project_errors, "source-index.jsonl"),
        "symbol_index": bool(symbols) and not matching_errors(project_errors, "symbol-index.jsonl"),
        "business_index": bool(business) and not matching_errors(project_errors, "business-index.jsonl"),
        "module_ownership": module_ownership_valid and not matching_errors(project_errors, "module-index.jsonl"),
        "route_evidence": evidence_group_valid("route_evidence"),
        "controller_evidence": evidence_group_valid("controller_evidence"),
        "validation_evidence": evidence_group_valid("validation_evidence"),
        "service_evidence": evidence_group_valid("service_evidence"),
        "persistence_evidence": evidence_group_valid("persistence_evidence"),
        "table_evidence": bool(apis) and all(isinstance(row.get("tables"), list) and row["tables"] and all(table in table_names for table in row["tables"]) for row in apis),
        "business_rules": has_type("business_rule") and not evidence_errors,
        "state_transitions": has_type("state_transition") and not evidence_errors,
        "transactions": evidence_group_valid("transaction_evidence"),
        "concurrency_or_idempotency": (has_type("idempotency_rule") or has_type("concurrency_rule")) and not evidence_errors,
        "side_effects": evidence_group_valid("side_effect_evidence"),
        "cross_module_dependencies": has_type("cross_module_dependency") and not evidence_errors,
        "current_evidence": bool(evidence) and not evidence_errors and not project_errors and not run_errors,
        "analysis_run_record": not run_errors and not document_errors,
    }
    results = [{"gate": name, "passed": checks[name]} for name in GATE_NAMES]
    status = "ANALYZED" if all(checks.values()) else "REVIEW_REQUIRED" if not checks["current_evidence"] else "PARTIAL"
    run_path = args.workspace / "analysis-runs" / args.project / f"{args.analysis_run_id}.json"
    try:
        run_record = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        run_record = {}
    run_finalized = (
        isinstance(run_record.get("finished_at"), str)
        and run_record.get("final_status") in {"COMPLETED", "PARTIAL", "REVIEW_REQUIRED", "BLOCKED"}
        and any(stage.get("name") == "quality_gates" for stage in run_record.get("stages", []) if isinstance(stage, dict))
    )
    committed_status = status if status != "ANALYZED" or run_finalized else "PARTIAL"
    report = {"project": args.project, "module": args.module, "analysis_run_id": args.analysis_run_id, "gate_count": len(results), "passed_count": sum(checks.values()), "status": status, "module_status_committed": committed_status, "run_finalized": run_finalized, "gates": results, "validation_errors": sorted(set(project_errors + evidence_errors + run_errors + document_errors))}
    output = args.workspace / "reports" / args.project / f"{args.module}-quality-gates.json"
    def update(rows):
        for row in rows:
            if row.get("module") == args.module:
                row["status"] = committed_status
                row["quality_gates"] = results
        return rows
    with exclusive_lock(root / "derived-indexes"):
        atomic_write(output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        locked_jsonl_update(root / "module-index.jsonl", update)
    print(f"QUALITY_GATES status={status} passed={report['passed_count']}/18 output={output}")
    return 0 if status == "ANALYZED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
