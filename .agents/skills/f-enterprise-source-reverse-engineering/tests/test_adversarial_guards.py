import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL = Path(__file__).parents[1]
SCRIPTS = SKILL / "scripts"
FIXTURE = SKILL / "tests/fixtures/mini-php-project"
sys.path.insert(0, str(SCRIPTS))
import run_analysis
from common.validation import REQUIRED_MODULE_DOCUMENTS


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, arguments)],
        capture_output=True,
        text=True,
    )


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class AdversarialGuardTest(unittest.TestCase):
    def prepare_real_workspace(self, directory):
        root = Path(directory) / "project-a"
        workspace = Path(directory) / "workspace"
        shutil.copytree(FIXTURE, root)
        result = run("build_source_index.py", "--project", "A", "--root", root, "--workspace", workspace)
        self.assertEqual(result.returncode, 0, result.stderr)
        index_path = workspace / "indexes/A/source-index.jsonl"
        rows = read_jsonl(index_path)
        for row in rows:
            row["modules"] = [{"module": "product", "role": "PRIMARY"}]
        write_jsonl(index_path, rows)
        return root, workspace

    def fake_workspace(self, directory):
        workspace = Path(directory) / "workspace"
        index = workspace / "indexes/A"
        run_id = "A-product-20260805-001"
        fake = {
            "project": "A",
            "file": "missing.php",
            "file_sha256": "0" * 64,
            "symbol": "Fake::run",
            "start_line": 999,
            "end_line": 999,
            "evidence_type": "implementation",
            "semantic_basis": "indexed_symbol",
            "confidence": "HIGH",
            "analysis_run_id": run_id,
            "status": "CURRENT",
        }
        write_jsonl(index / "source-index.jsonl", [{
            "project": "A",
            "repository_root": "/",
            "relative_path": "missing.php",
            "absolute_path": "/missing.php",
            "size_bytes": 1,
            "mtime": 1.0,
            "mtime_ns": 1,
            "sha256": "0" * 64,
            "line_count": 1,
            "analysis_status": "ANALYZED",
            "modules": [{"module": "product", "role": "PRIMARY"}],
        }])
        write_jsonl(index / "symbol-index.jsonl", [{"project": "A", "fully_qualified_name": "Fake::run"}])
        write_jsonl(index / "module-index.jsonl", [{"project": "A", "module": "product", "status": "PARTIAL", "primary_files": ["missing.php"], "quality_gates": []}])
        api = {
            "project": "A",
            "module": "product",
            "api_id": "A-PRODUCT-API-001",
            "method": "POST",
            "path": "/fake",
            "analysis_run_id": run_id,
            "evidence": 1,
            "route_evidence": [fake],
            "controller_evidence": [fake],
            "validation_evidence": [fake],
            "service_evidence": [fake],
            "persistence_evidence": [fake],
            "side_effect_evidence": [fake],
            "transaction_evidence": [fake],
            "tables": ["fake_table"],
            "coverage": {dimension: {"status": "PRESENT", "rationale": "fabricated"} for dimension in ("validation", "service", "persistence", "transaction", "side_effect", "tables")},
            "candidates": [],
            "status": "ANALYZED",
        }
        write_jsonl(index / "api-index.jsonl", [api])
        business = []
        for number, kind in enumerate(("business_rule", "state_transition", "idempotency_rule", "cross_module_dependency"), 1):
            business.append({
                "project": "A",
                "module": "product",
                "business_id": f"A-FAKE-{number}",
                "type": kind,
                "name": kind,
                "classification": "FACT",
                "confidence": "HIGH",
                "evidence": [fake],
                "analysis_run_id": run_id,
                "status": "ANALYZED",
            })
        write_jsonl(index / "business-index.jsonl", business)
        run_path = workspace / f"analysis-runs/A/{run_id}.json"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_text("{}\n", encoding="utf-8")
        return workspace, run_id

    def test_quality_gate_rejects_fabricated_and_malformed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace, run_id = self.fake_workspace(directory)
            result = run(
                "evaluate_quality_gates.py",
                "--project", "A",
                "--module", "product",
                "--analysis-run-id", run_id,
                "--workspace", workspace,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertNotEqual(report["status"], "ANALYZED")
            self.assertTrue(report["validation_errors"])
            self.assertTrue(any("missing" in error or "invalid" in error for error in report["validation_errors"]))

    def test_validate_indexes_rejects_fabricated_indexes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace, _ = self.fake_workspace(directory)
            result = run("validate_indexes.py", "--workspace", workspace, "--project", "A")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("INDEX_INVALID", result.stdout)
            self.assertNotIn("INDEXES_OK", result.stdout)

    def test_stale_detection_keeps_same_named_module_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            roots = {}
            for project in ("A", "B"):
                root = Path(directory) / f"project-{project.lower()}"
                roots[project] = root
                shutil.copytree(FIXTURE, root)
                result = run("build_source_index.py", "--project", project, "--root", root, "--workspace", workspace)
                self.assertEqual(result.returncode, 0, result.stderr)
                index = workspace / f"indexes/{project}/source-index.jsonl"
                result = run("update_module_ownership.py", "--index", index, "--file", "app/Models/Product.php", "--module", "product", "--role", "PRIMARY")
                self.assertEqual(result.returncode, 0, result.stderr)
                result = run("build_module_index.py", "--project", project, "--workspace", workspace)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = read_jsonl(workspace / f"indexes/{project}/module-index.jsonl")
                rows[0]["status"] = "ANALYZED"
                write_jsonl(workspace / f"indexes/{project}/module-index.jsonl", rows)
            target = roots["A"] / "app/Models/Product.php"
            target.write_text(target.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")
            result = run("detect_stale_references.py", "--workspace", workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(read_jsonl(workspace / "indexes/A/module-index.jsonl")[0]["status"], "REVIEW_REQUIRED")
            self.assertEqual(read_jsonl(workspace / "indexes/B/module-index.jsonl")[0]["status"], "ANALYZED")
            report = json.loads((workspace / "reports/stale-references.json").read_text(encoding="utf-8"))
            self.assertEqual(report["affected_by_project"]["A"]["modules"], ["product"])
            self.assertEqual(report["affected_by_project"]["B"]["modules"], [])

    def test_run_analysis_rejects_failed_gate_even_with_old_analyzed_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project-a"
            workspace = Path(directory) / "workspace"
            root.mkdir()
            report_path = workspace / "reports/A/product-quality-gates.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps({
                "project": "A",
                "module": "product",
                "analysis_run_id": "A-product-20260805-002",
                "status": "ANALYZED",
                "gates": [],
            }), encoding="utf-8")
            manifest_path = workspace / "indexes/A/index-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps({
                "project": "A", "repository_root": str(root.resolve()), "snapshot_id": "a" * 64,
            }), encoding="utf-8")
            successes = [subprocess.CompletedProcess([], 0, "OK", "") for _ in range(7)]
            failed_gate = subprocess.CompletedProcess([], 1, "", "gate crashed")
            arguments = [
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", str(root), "--workspace", str(workspace),
                "--analysis-run-id", "A-product-20260805-002",
            ]
            with mock.patch.object(run_analysis.subprocess, "run", side_effect=successes + [failed_gate]), mock.patch.object(run_analysis, "refresh_file_record"), mock.patch.object(sys, "argv", arguments):
                result = run_analysis.main()
            self.assertEqual(result, 1)
            record = json.loads((workspace / "analysis-runs/A/A-product-20260805-002.json").read_text(encoding="utf-8"))
            self.assertEqual(record["final_status"], "FAILED")
            self.assertIn("quality gate process failed", record["error"])

    def test_quality_gate_rejects_reused_evidence_without_semantic_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare_real_workspace(directory)
            run_id = "A-product-20260805-001"
            result = run(
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", root, "--sql-root", root / "database",
                "--workspace", workspace, "--analysis-run-id", run_id,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            business_path = workspace / "indexes/A/business-index.jsonl"
            rows = read_jsonl(business_path)
            real_evidence = next(row["evidence"][0] for row in rows if row.get("type") == "business_rule")
            for number, kind in enumerate(("state_transition", "idempotency_rule", "cross_module_dependency"), 1):
                rows.append({
                    "project": "A", "module": "product", "business_id": f"A-EMPTY-{number}",
                    "type": kind, "name": kind, "classification": "FACT", "confidence": "HIGH",
                    "evidence": [dict(real_evidence)], "related_apis": [], "related_tables": [],
                    "analysis_run_id": run_id, "status": "ANALYZED",
                })
            write_jsonl(business_path, rows)
            result = run(
                "evaluate_quality_gates.py", "--project", "A", "--module", "product",
                "--analysis-run-id", run_id, "--workspace", workspace,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertNotEqual(report["status"], "ANALYZED")
            self.assertTrue(any("semantic fields" in error for error in report["validation_errors"]))

    def test_path_like_module_and_run_ids_are_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project-a"
            workspace = Path(directory) / "workspace"
            shutil.copytree(FIXTURE, root)
            result = run(
                "run_analysis.py", "--project", "A", "--module", "../escape",
                "--root", root, "--workspace", workspace,
                "--analysis-run-id", "../escape",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((workspace / "analysis-runs/escape.json").exists())

    def test_evidence_verifier_rejects_route_symbol_without_route_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare_real_workspace(directory)
            for script, arguments in (
                ("build_symbol_index.py", ("--project", "A", "--workspace", workspace)),
                ("extract_php_routes.py", ("--project", "A", "--root", root, "--workspace", workspace)),
            ):
                result = run(script, *arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
            source = next(row for row in read_jsonl(workspace / "indexes/A/source-index.jsonl") if row["relative_path"].endswith("ProductController.php"))
            evidence = {
                "project": "A", "file": source["relative_path"], "file_sha256": source["sha256"],
                "symbol": "route declaration", "start_line": 1, "end_line": 1,
                "evidence_type": "route", "semantic_basis": "indexed_route_declaration", "confidence": "HIGH",
                "analysis_run_id": "A-product-20260805-001", "status": "CURRENT",
            }
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            result = run("verify_source_evidence.py", "--workspace", workspace, "--evidence", evidence_path)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("route", result.stdout.lower())

    def test_downstream_indexer_rejects_cross_project_source_row(self):
        with tempfile.TemporaryDirectory() as directory:
            _, workspace = self.prepare_real_workspace(directory)
            source_path = workspace / "indexes/A/source-index.jsonl"
            rows = read_jsonl(source_path)
            rows[0]["project"] = "B"
            write_jsonl(source_path, rows)
            result = run("build_symbol_index.py", "--project", "A", "--workspace", workspace)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project mismatch", result.stderr)

    def test_incremental_indexer_rejects_cross_project_cached_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            _, workspace = self.prepare_real_workspace(directory)
            first = run("build_symbol_index.py", "--project", "A", "--workspace", workspace)
            self.assertEqual(first.returncode, 0, first.stderr)
            symbol_path = workspace / "indexes/A/symbol-index.jsonl"
            rows = read_jsonl(symbol_path)
            rows[0]["project"] = "B"
            write_jsonl(symbol_path, rows)
            result = run("build_symbol_index.py", "--project", "A", "--workspace", workspace)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project mismatch", result.stderr)

    def test_analyzed_status_is_committed_only_after_documents_and_final_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare_real_workspace(directory)
            run_id = "A-product-20260805-001"
            result = run(
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", root, "--sql-root", root / "database",
                "--workspace", workspace, "--analysis-run-id", run_id,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            business_path = workspace / "indexes/A/business-index.jsonl"
            rows = read_jsonl(business_path)
            evidence = dict(next(row["evidence"][0] for row in rows if row.get("type") == "business_rule"))
            rows.extend([
                {"project": "A", "module": "product", "business_id": "A-STATE-001", "type": "state_transition", "name": "draft transition", "classification": "FACT", "confidence": "HIGH", "evidence": [dict(evidence)], "related_apis": [], "related_tables": ["products"], "analysis_run_id": run_id, "status": "ANALYZED", "entity": "product", "from_state": "NEW", "to_state": "DRAFT", "trigger": "create"},
                {"project": "A", "module": "product", "business_id": "A-IDEMPOTENCY-001", "type": "idempotency_rule", "name": "sku uniqueness", "classification": "FACT", "confidence": "HIGH", "evidence": [dict(evidence)], "related_apis": [], "related_tables": ["products"], "analysis_run_id": run_id, "status": "ANALYZED", "scenario": "duplicate create", "mechanism": "unique sku"},
                {"project": "A", "module": "product", "business_id": "A-DEPENDENCY-001", "type": "cross_module_dependency", "name": "inventory call", "classification": "FACT", "confidence": "HIGH", "evidence": [dict(evidence)], "related_apis": [], "related_tables": [], "related_modules": ["inventory"], "dependency_type": "call", "direction": "downstream", "analysis_run_id": run_id, "status": "ANALYZED"},
            ])
            write_jsonl(business_path, rows)
            document_root = workspace / "reverse-docs/project-a/modules/product"
            document_root.mkdir(parents=True)
            for name in REQUIRED_MODULE_DOCUMENTS:
                (document_root / name).write_text(f"# {name}\n\nFACT: verified by A-product evidence with current hash and source lines.\n", encoding="utf-8")
            run_path = workspace / f"analysis-runs/A/{run_id}.json"
            finalized = json.loads(run_path.read_text(encoding="utf-8"))
            in_progress = dict(finalized)
            in_progress["finished_at"] = None
            in_progress["final_status"] = "RUNNING"
            in_progress["stages"] = finalized["stages"][:-1]
            run_path.write_text(json.dumps(in_progress), encoding="utf-8")
            gate_args = ("--project", "A", "--module", "product", "--analysis-run-id", run_id, "--workspace", workspace)
            candidate = run("evaluate_quality_gates.py", *gate_args)
            self.assertEqual(candidate.returncode, 0, candidate.stderr + candidate.stdout)
            report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "ANALYZED")
            self.assertEqual(report["module_status_committed"], "PARTIAL")
            self.assertNotEqual(read_jsonl(workspace / "indexes/A/module-index.jsonl")[0]["status"], "ANALYZED")
            run_path.write_text(json.dumps(finalized), encoding="utf-8")
            direct = run("evaluate_quality_gates.py", *gate_args)
            self.assertEqual(direct.returncode, 0, direct.stderr + direct.stdout)
            self.assertNotEqual(read_jsonl(workspace / "indexes/A/module-index.jsonl")[0]["status"], "ANALYZED")
            committed = run(
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", root, "--sql-root", root / "database", "--workspace", workspace,
                "--analysis-run-id", run_id, "--finalize",
            )
            self.assertEqual(committed.returncode, 0, committed.stderr + committed.stdout)
            self.assertEqual(read_jsonl(workspace / "indexes/A/module-index.jsonl")[0]["status"], "ANALYZED")
            self.assertTrue(all(row["status"] == "ANALYZED" for row in read_jsonl(workspace / "indexes/A/api-index.jsonl") if row.get("module") == "product"))
            self.assertTrue(all(row["status"] == "ANALYZED" for row in read_jsonl(workspace / "indexes/A/business-index.jsonl") if row.get("module") == "product" and row.get("analysis_run_id") == run_id))
            final_record = json.loads(run_path.read_text(encoding="utf-8"))
            self.assertEqual(final_record["finalization_count"], 1)
            self.assertEqual(len(final_record["quality_gate_attempts"]), 1)
            repeated = run("evaluate_quality_gates.py", *gate_args)
            self.assertEqual(repeated.returncode, 0, repeated.stderr + repeated.stdout)
            self.assertEqual(read_jsonl(workspace / "indexes/A/module-index.jsonl")[0]["status"], "ANALYZED")
            repeated_report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertFalse(repeated_report["commit_performed"])


if __name__ == "__main__":
    unittest.main()
