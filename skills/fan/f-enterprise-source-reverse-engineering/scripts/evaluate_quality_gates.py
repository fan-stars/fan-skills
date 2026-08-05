#!/usr/bin/env python3
"""Evaluate 18 executable gates and prevent incomplete modules becoming ANALYZED."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, locked_jsonl_update, read_jsonl

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
    evidence = [item for row in business + apis for key, value in row.items() if key == "evidence" or key.endswith("_evidence") for item in value if isinstance(value, list) and isinstance(item, dict)]
    has_type = lambda kind: any(row.get("type") == kind for row in business)
    checks = {
        "source_index": bool(source), "symbol_index": bool(symbols), "business_index": bool(business),
        "module_ownership": bool(module and module.get("primary_files")),
        "route_evidence": bool(apis and all(row.get("route_evidence") for row in apis)),
        "controller_evidence": bool(apis and all(row.get("controller_evidence") for row in apis)),
        "validation_evidence": bool(apis and all(row.get("validation_evidence") for row in apis)),
        "service_evidence": bool(apis and all(row.get("service_evidence") for row in apis)),
        "persistence_evidence": bool(apis and all(row.get("persistence_evidence") for row in apis)),
        "table_evidence": bool(apis and all(row.get("tables") for row in apis)),
        "business_rules": has_type("business_rule"), "state_transitions": has_type("state_transition"),
        "transactions": bool(apis and all(row.get("transaction_evidence") for row in apis)),
        "concurrency_or_idempotency": has_type("idempotency_rule") or has_type("concurrency_rule"),
        "side_effects": bool(apis and all(row.get("side_effect_evidence") for row in apis)),
        "cross_module_dependencies": has_type("cross_module_dependency"),
        "current_evidence": bool(evidence) and all(item.get("status", "CURRENT") == "CURRENT" for item in evidence),
        "analysis_run_record": (args.workspace / "analysis-runs" / args.project / f"{args.analysis_run_id}.json").exists(),
    }
    results = [{"gate": name, "passed": checks[name]} for name in GATE_NAMES]
    status = "ANALYZED" if all(checks.values()) else "REVIEW_REQUIRED" if not checks["current_evidence"] else "PARTIAL"
    report = {"project": args.project, "module": args.module, "analysis_run_id": args.analysis_run_id, "gate_count": len(results), "passed_count": sum(checks.values()), "status": status, "gates": results}
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
