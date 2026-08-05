#!/usr/bin/env python3
"""Evaluate 18 executable gates and prevent incomplete modules becoming ANALYZED."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, locked_jsonl_update, read_jsonl
from common.validation import (
    evidence_fields,
    matching_errors,
    validate_evidence,
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
    root = args.workspace / "indexes" / args.project
    source = read_jsonl(root / "source-index.jsonl")
    symbols = read_jsonl(root / "symbol-index.jsonl")
    business = [row for row in read_jsonl(root / "business-index.jsonl") if row.get("module") == args.module]
    apis = [row for row in read_jsonl(root / "api-index.jsonl") if row.get("module") == args.module]
    modules = read_jsonl(root / "module-index.jsonl")
    module = next((row for row in modules if row.get("module") == args.module), None)
    project_errors = validate_project_indexes(args.workspace, args.project)
    source_by_file = {row.get("relative_path"): row for row in source if isinstance(row.get("relative_path"), str)}
    routes = read_jsonl(root / "routes.jsonl")
    tables = read_jsonl(root / "table-index.jsonl")
    evidence = []
    evidence_errors = []
    for row_number, row in enumerate(business + apis):
        items, structural_errors = evidence_fields(row)
        evidence.extend(items)
        evidence_errors.extend(f"record {row_number}: {error}" for error in structural_errors)
        for item_number, item in enumerate(items):
            errors = validate_evidence(item, args.project, source_by_file, symbols, routes, args.analysis_run_id)
            evidence_errors.extend(f"record {row_number} evidence {item_number}: {error}" for error in errors)
    run_errors = validate_run_record(args.workspace, args.project, args.analysis_run_id, args.module)
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
        return bool(apis) and all(isinstance(row.get(key), list) and row[key] for row in apis) and not evidence_errors
    has_type = lambda kind: any(row.get("type") == kind for row in business)
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
        "analysis_run_record": not run_errors,
    }
    results = [{"gate": name, "passed": checks[name]} for name in GATE_NAMES]
    status = "ANALYZED" if all(checks.values()) else "REVIEW_REQUIRED" if not checks["current_evidence"] else "PARTIAL"
    report = {"project": args.project, "module": args.module, "analysis_run_id": args.analysis_run_id, "gate_count": len(results), "passed_count": sum(checks.values()), "status": status, "gates": results, "validation_errors": sorted(set(project_errors + evidence_errors + run_errors))}
    output = args.workspace / "reports" / args.project / f"{args.module}-quality-gates.json"
    atomic_write(output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    def update(rows):
        for row in rows:
            if row.get("module") == args.module:
                row["status"] = status
                row["quality_gates"] = results
        return rows
    locked_jsonl_update(root / "module-index.jsonl", update)
    print(f"QUALITY_GATES status={status} passed={report['passed_count']}/18 output={output}")
    return 0 if status == "ANALYZED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
