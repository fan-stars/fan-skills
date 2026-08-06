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
    parser.add_argument("--trust-source-index", action="store_true")
    parser.add_argument("--source-snapshot-id")
    args = parser.parse_args()
    if args.trust_source_index and not args.source_snapshot_id:
        parser.error("--trust-source-index requires --source-snapshot-id")
    if args.source_snapshot_id and not args.trust_source_index:
        parser.error("--source-snapshot-id requires --trust-source-index")
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
    project_errors = validate_project_indexes(
        args.workspace, args.project, args.module, allow_in_progress_runs=True,
        trust_source_index=args.trust_source_index, source_snapshot_id=args.source_snapshot_id,
    )
    if source_load_error:
        project_errors.append(f"source-index.jsonl: {source_load_error}")
    source_by_file = {row.get("relative_path"): row for row in source if isinstance(row.get("relative_path"), str)}
    evidence = []
    evidence_errors = []
    fingerprint_cache = {
        row["relative_path"]: (row.get("sha256"), row.get("line_count"))
        for row in source
    } if args.trust_source_index and not source_load_error else {}
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
            if not isinstance(item, dict) or item.get("evidence_type") != "transaction":
                continue
            symbol = symbols_by_name.get(item.get("symbol")) if isinstance(item, dict) else None
            if symbol is not None and not any("DB::transaction" in call for call in symbol.get("calls", [])):
                api_link_errors.append(f"API {api.get('api_id')}: transaction evidence has no transaction call")
        for item in api.get("side_effect_evidence", []):
            if not isinstance(item, dict) or item.get("evidence_type") != "side_effect":
                continue
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
    def coverage_valid(dimension: str, key: str | None, expected: str | None) -> bool:
        if not apis:
            return False
        for api in apis:
            detail = api.get("coverage", {}).get(dimension, {})
            status = detail.get("status")
            if not isinstance(detail.get("rationale"), str) or not detail["rationale"].strip():
                return False
            if dimension == "tables":
                if status == "PRESENT" and api.get("tables") and all(table in table_names for table in api["tables"]):
                    continue
                if status == "NOT_APPLICABLE" and api.get("coverage", {}).get("persistence", {}).get("status") == "NOT_APPLICABLE":
                    continue
                return False
            values = api.get(key, [])
            required_type = expected if status == "PRESENT" else f"{expected}_absence"
            if status not in {"PRESENT", "NOT_APPLICABLE"} or not values:
                return False
            if any(not isinstance(item, dict) or item.get("evidence_type") != required_type for item in values):
                return False
            if status == "NOT_APPLICABLE" and any(item.get("semantic_basis") != "reviewed_negative_evidence" for item in values):
                return False
        return not evidence_errors
    has_type = lambda kind: any(row.get("type") == kind and isinstance(row.get("evidence"), list) and row["evidence"] for row in business)
    def business_dimension_valid(present_types: tuple[str, ...], absence_type: str) -> bool:
        if any(has_type(kind) for kind in present_types):
            return not evidence_errors
        return any(
            row.get("type") == absence_type
            and isinstance(row.get("rationale"), str) and row["rationale"].strip()
            and isinstance(row.get("evidence"), list) and row["evidence"]
            and isinstance(row.get("reviewer"), str) and row["reviewer"].strip()
            and isinstance(row.get("reviewed_at"), str) and row["reviewed_at"].strip()
            and all(
                isinstance(item, dict)
                and item.get("evidence_type") == absence_type
                and item.get("semantic_basis") == "reviewed_negative_evidence"
                for item in row["evidence"]
            )
            for row in business
        ) and not evidence_errors
    checks = {
        "source_index": bool(source) and not matching_errors(project_errors, "source-index.jsonl"),
        "symbol_index": bool(symbols) and not matching_errors(project_errors, "symbol-index.jsonl"),
        "business_index": bool(business) and not matching_errors(project_errors, "business-index.jsonl"),
        "module_ownership": module_ownership_valid and not matching_errors(project_errors, "module-index.jsonl"),
        "route_evidence": evidence_group_valid("route_evidence"),
        "controller_evidence": evidence_group_valid("controller_evidence"),
        "validation_evidence": coverage_valid("validation", "validation_evidence", "validation"),
        "service_evidence": coverage_valid("service", "service_evidence", "service"),
        "persistence_evidence": coverage_valid("persistence", "persistence_evidence", "persistence"),
        "table_evidence": coverage_valid("tables", None, None),
        "business_rules": business_dimension_valid(("business_rule",), "business_rule_absence"),
        "state_transitions": business_dimension_valid(("state_transition",), "state_transition_absence"),
        "transactions": coverage_valid("transaction", "transaction_evidence", "transaction"),
        "concurrency_or_idempotency": business_dimension_valid(("idempotency_rule", "concurrency_rule"), "concurrency_idempotency_absence"),
        "side_effects": coverage_valid("side_effect", "side_effect_evidence", "side_effect"),
        "cross_module_dependencies": business_dimension_valid(("cross_module_dependency",), "cross_module_dependency_absence"),
        "current_evidence": bool(evidence) and not evidence_errors and not project_errors and not run_errors,
        "analysis_run_record": not run_errors and not document_errors,
    }
    results = [{"gate": name, "passed": checks[name]} for name in GATE_NAMES]
    status = "ANALYZED" if all(checks.values()) else "REVIEW_REQUIRED" if not checks["current_evidence"] else "PARTIAL"
    # A gate evaluation is only a candidate result.  The orchestrator owns the
    # final run-record validation and the atomic ANALYZED commit.
    preserve_analyzed = (
        status == "ANALYZED"
        and isinstance(module, dict)
        and module.get("status") == "ANALYZED"
        and module.get("last_analysis_run_id") == args.analysis_run_id
    )
    committed_status = "ANALYZED" if preserve_analyzed else "PARTIAL" if status == "ANALYZED" else status
    report = {"project": args.project, "module": args.module, "analysis_run_id": args.analysis_run_id, "gate_count": len(results), "passed_count": sum(checks.values()), "status": status, "module_status_committed": committed_status, "commit_performed": False, "run_finalized": preserve_analyzed, "finalization_required": status == "ANALYZED" and not preserve_analyzed, "gates": results, "validation_errors": sorted(set(project_errors + evidence_errors + run_errors + document_errors))}
    output = args.workspace / "reports" / args.project / f"{args.module}-quality-gates.json"
    def update(rows):
        for row in rows:
            if row.get("module") == args.module:
                row["status"] = committed_status
                row["quality_gates"] = results
                if committed_status == "ANALYZED":
                    row["last_analysis_run_id"] = args.analysis_run_id
        return rows
    def update_records(rows):
        for row in rows:
            if row.get("module") == args.module and row.get("analysis_run_id") == args.analysis_run_id:
                if not (preserve_analyzed and row.get("status") == "ANALYZED"):
                    row["status"] = committed_status
        return rows
    with exclusive_lock(root / "derived-indexes"):
        atomic_write(output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        locked_jsonl_update(root / "module-index.jsonl", update)
        locked_jsonl_update(root / "api-index.jsonl", update_records)
        locked_jsonl_update(root / "business-index.jsonl", update_records)
    print(f"QUALITY_GATES status={status} passed={report['passed_count']}/18 output={output}")
    return 0 if status == "ANALYZED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
