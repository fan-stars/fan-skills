import json
import unittest
from pathlib import Path

from jsonschema import validators

SKILL = Path(__file__).parents[1]
SCHEMAS = SKILL / "schemas"

EVIDENCE = {"project": "A", "file": "app/a.php", "file_sha256": "a" * 64, "symbol": "A::run", "start_line": 1, "end_line": 2, "evidence_type": "implementation", "confidence": "HIGH", "analysis_run_id": "A-product-20260805-001", "status": "CURRENT"}
VALID_INSTANCES = {
    "workspace-config.schema.json": {"version": 1, "projects": {"A": {}, "B": {}}},
    "project-manifest.schema.json": {"project": "A", "repository_root": "/repo/a", "source_index_version": 1},
    "analysis-run.schema.json": {"analysis_run_id": "A-product-20260805-001", "project": "A", "requested_module": "product", "started_at": "2026-08-05T00:00:00Z", "finished_at": "2026-08-05T00:00:01Z", "source_root": "/repo/a", "workspace": "/work", "stages": [{"name": "source", "command": ["python", "script.py"], "exit_code": 0}], "files_read": [], "files_written": [], "stale_evidence": [], "unresolved_questions": [], "final_status": "PARTIAL"},
    "source-index.schema.json": {"project": "A", "repository_root": "/repo/a", "relative_path": "app/a.php", "absolute_path": "/repo/a/app/a.php", "size_bytes": 1, "mtime": 1.0, "mtime_ns": 1000000000, "sha256": "a" * 64, "line_count": 1, "analysis_status": "UNREAD", "modules": []},
    "symbol-index.schema.json": {"project": "A", "symbol_id": "A:app/a.php:A", "file": "app/a.php", "file_sha256": "a" * 64, "symbol_type": "class", "name": "A", "fully_qualified_name": "A", "start_line": 1, "end_line": 2, "calls": [], "called_by": []},
    "business-index.schema.json": {"project": "A", "business_id": "A-X-RULE-001", "type": "business_rule", "module": "product", "name": "draft rule", "classification": "FACT", "confidence": "HIGH", "evidence": [EVIDENCE], "related_apis": ["A-API-001"], "related_tables": ["products"], "analysis_run_id": "A-product-20260805-001", "status": "ANALYZED"},
    "module-index.schema.json": {"project": "A", "module": "product", "status": "PARTIAL", "primary_files": [], "secondary_files": [], "shared_files": [], "quality_gates": []},
    "api-index.schema.json": {"project": "A", "module": "product", "api_id": "A-API-001", "method": "POST", "path": "/api/products", "route_evidence": [EVIDENCE], "controller_evidence": [EVIDENCE], "validation_evidence": [EVIDENCE], "service_evidence": [EVIDENCE], "persistence_evidence": [EVIDENCE], "side_effect_evidence": [EVIDENCE], "tables": ["products"], "analysis_run_id": "A-product-20260805-001", "status": "ANALYZED"},
    "route-index.schema.json": {"project": "A", "file": "routes/api.php", "file_sha256": "a" * 64, "start_line": 1, "end_line": 1, "method": "POST", "path": "/api/products", "classification": "CANDIDATE", "confidence": "MEDIUM"},
    "table-index.schema.json": {"project": "A", "table": "products", "file": "database/products.sql", "file_sha256": "a" * 64, "start_line": 1, "end_line": 1, "classification": "FACT", "confidence": "HIGH"},
    "evidence.schema.json": EVIDENCE,
    "decision-record.schema.json": {"decision_id": "JAVA-PRODUCT-001", "decision_type": "MERGE", "sources": ["A-PRODUCT-001", "B-PRODUCT-001"], "reason": "保留双方已验证能力"},
}


class SchemaTest(unittest.TestCase):
    def test_all_schemas_are_valid_and_accept_a_real_instance(self):
        schemas = sorted(SCHEMAS.glob("*.json"))
        self.assertEqual(len(schemas), 12)
        self.assertEqual(set(VALID_INSTANCES), {path.name for path in schemas})
        for path in schemas:
            schema = json.loads(path.read_text(encoding="utf-8"))
            validator_class = validators.validator_for(schema)
            validator_class.check_schema(schema)
            validator_class(schema).validate(VALID_INSTANCES[path.name])


if __name__ == "__main__":
    unittest.main()
