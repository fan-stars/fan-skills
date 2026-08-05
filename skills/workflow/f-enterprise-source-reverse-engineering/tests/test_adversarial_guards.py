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
            successes = [subprocess.CompletedProcess([], 0, "OK", "") for _ in range(6)]
            failed_gate = subprocess.CompletedProcess([], 1, "", "gate crashed")
            arguments = [
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", str(root), "--workspace", str(workspace),
                "--analysis-run-id", "A-product-20260805-002",
            ]
            with mock.patch.object(run_analysis.subprocess, "run", side_effect=successes + [failed_gate]), mock.patch.object(sys, "argv", arguments):
                result = run_analysis.main()
            self.assertEqual(result, 1)
            record = json.loads((workspace / "analysis-runs/A/A-product-20260805-002.json").read_text(encoding="utf-8"))
            self.assertEqual(record["final_status"], "FAILED")
            self.assertIn("quality gate process failed", record["error"])


if __name__ == "__main__":
    unittest.main()
