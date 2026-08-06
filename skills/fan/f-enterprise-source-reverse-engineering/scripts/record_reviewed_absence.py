#!/usr/bin/env python3
"""Safely record a human-reviewed NOT_APPLICABLE conclusion for one API dimension."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common.core import exclusive_lock, load_isolated_source_index, read_project_jsonl, validate_analysis_run_id, validate_module_name, write_jsonl
from common.validation import validate_evidence


API_DIMENSIONS = {
    "validation": "validation",
    "service": "service",
    "persistence": "persistence",
    "transaction": "transaction",
    "side_effect": "side_effect",
}
BUSINESS_DIMENSIONS = {
    "business_rule": "business_rule_absence",
    "state_transition": "state_transition_absence",
    "concurrency_or_idempotency": "concurrency_idempotency_absence",
    "cross_module_dependency": "cross_module_dependency_absence",
}


def reviewed_anchor(api: dict, project: str, run_id: str, source: list[dict], symbols: list[dict], routes: list[dict]) -> dict:
    evidence = next((item for item in api.get("controller_evidence", []) if isinstance(item, dict)), None)
    if evidence is None:
        raise ValueError(f"API {api.get('api_id')} has no controller evidence to anchor a reviewed absence")
    errors = validate_evidence(
        evidence, project,
        {row["relative_path"]: row for row in source}, symbols, routes,
        expected_run_id=run_id,
    )
    if errors:
        raise ValueError("controller evidence is not current: " + "; ".join(errors))
    return dict(evidence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--api-id", required=True)
    parser.add_argument("--dimension", choices=tuple(API_DIMENSIONS) + tuple(BUSINESS_DIMENSIONS), required=True)
    parser.add_argument("--rationale", required=True, help="what complete reachable scope was reviewed and why the dimension does not apply")
    parser.add_argument("--reviewer", required=True, help="human reviewer or ticket identity")
    parser.add_argument("--reviewed-at", help="ISO-8601 timestamp; defaults to current UTC time")
    parser.add_argument("--analysis-run-id", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_module_name(args.module)
        validate_analysis_run_id(args.analysis_run_id, args.project, args.module)
    except ValueError as exc:
        parser.error(str(exc))
    if not args.rationale.strip() or not args.reviewer.strip():
        parser.error("--rationale and --reviewer must be non-empty")
    reviewed_at = args.reviewed_at or datetime.now(timezone.utc).isoformat()
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError:
        parser.error("--reviewed-at must be an ISO-8601 timestamp")

    run_path = args.workspace / "analysis-runs" / args.project / f"{args.analysis_run_id}.json"
    try:
        run_record = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"analysis run is unreadable: {exc}")
    if run_record.get("final_status") not in {"PARTIAL", "REVIEW_REQUIRED"}:
        parser.error("reviewed absence must enrich a PARTIAL or REVIEW_REQUIRED run; use --finalize after writing it")

    index_dir = args.workspace / "indexes" / args.project
    try:
        source = load_isolated_source_index(args.workspace, args.project)
        symbols = read_project_jsonl(index_dir / "symbol-index.jsonl", args.project)
        routes = read_project_jsonl(index_dir / "routes.jsonl", args.project)
    except ValueError as exc:
        parser.error(str(exc))

    with exclusive_lock(index_dir / "derived-indexes"):
        apis = read_project_jsonl(index_dir / "api-index.jsonl", args.project)
        business = read_project_jsonl(index_dir / "business-index.jsonl", args.project)
        api = next((row for row in apis if row.get("api_id") == args.api_id and row.get("module") == args.module), None)
        if api is None:
            parser.error(f"API not found in module: {args.api_id}")
        if api.get("analysis_run_id") != args.analysis_run_id:
            parser.error("API analysis_run_id does not match the requested run")
        anchor = reviewed_anchor(api, args.project, args.analysis_run_id, source, symbols, routes)
        anchor.update({
            "evidence_type": f"{API_DIMENSIONS[args.dimension]}_absence" if args.dimension in API_DIMENSIONS else BUSINESS_DIMENSIONS[args.dimension],
            "semantic_basis": "reviewed_negative_evidence",
            "confidence": "HIGH",
            "reviewer": args.reviewer.strip(),
            "reviewed_at": reviewed_at,
            "status": "CURRENT",
        })

        if args.dimension in API_DIMENSIONS:
            evidence_key = f"{API_DIMENSIONS[args.dimension]}_evidence"
            coverage = api.setdefault("coverage", {})
            detail = coverage.setdefault(args.dimension, {})
            if detail.get("status") == "PRESENT":
                parser.error(f"{args.dimension} is PRESENT; resolve the conflicting fact before recording absence")
            detail.update({"status": "NOT_APPLICABLE", "rationale": args.rationale.strip()})
            api[evidence_key] = [anchor]
            api["status"] = "PARTIAL"
        else:
            absence_type = BUSINESS_DIMENSIONS[args.dimension]
            present_types = {
                "business_rule": "business_rule",
                "state_transition": "state_transition",
                "concurrency_or_idempotency": ("idempotency_rule", "concurrency_rule"),
                "cross_module_dependency": "cross_module_dependency",
            }[args.dimension]
            types = present_types if isinstance(present_types, tuple) else (present_types,)
            if any(
                row.get("type") in types and args.api_id in row.get("related_apis", [])
                for row in business
            ):
                parser.error(f"{args.dimension} has a PRESENT fact related to {args.api_id}; resolve the conflict first")
            existing = next((row for row in business if row.get("type") == absence_type and args.api_id in row.get("related_apis", [])), None)
            if existing is None:
                sequence = 1 + sum(row.get("type") == absence_type for row in business)
                existing = {
                    "project": args.project, "business_id": f"{args.project}-{args.module.upper()}-{absence_type.replace('_', '-')}-{sequence:03d}",
                    "type": absence_type, "module": args.module, "name": f"{args.dimension} is not applicable to {args.api_id}",
                    "classification": "FACT", "confidence": "HIGH", "evidence": [], "related_apis": [args.api_id],
                    "related_tables": api.get("tables", []), "analysis_run_id": args.analysis_run_id, "status": "PARTIAL",
                }
                business.append(existing)
            existing.update({"rationale": args.rationale.strip(), "reviewer": args.reviewer.strip(), "reviewed_at": reviewed_at, "evidence": [anchor], "related_apis": [args.api_id], "related_tables": api.get("tables", []), "analysis_run_id": args.analysis_run_id, "status": "PARTIAL"})

        module_path = index_dir / "module-index.jsonl"
        modules = read_project_jsonl(module_path, args.project)
        for row in modules:
            if row.get("module") == args.module and row.get("status") == "ANALYZED":
                row["status"] = "REVIEW_REQUIRED"
        write_jsonl(index_dir / "api-index.jsonl", apis)
        write_jsonl(index_dir / "business-index.jsonl", business)
        write_jsonl(module_path, modules)
    print(f"REVIEWED_ABSENCE_OK project={args.project} module={args.module} api={args.api_id} dimension={args.dimension} run={args.analysis_run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
