import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1]
FIXTURE = SKILL / "tests/fixtures/mini-php-project"
SCRIPTS = SKILL / "scripts"
MODULE_FILES = [
    "routes/api.php", "app/Http/Controllers/ProductController.php", "app/Http/Requests/ProductRequest.php",
    "app/Services/ProductService.php", "app/Services/InventoryService.php", "app/Repositories/ProductRepository.php",
    "app/Models/Product.php", "app/Jobs/SyncProductJob.php", "database/products.sql", "database/product_skus.sql",
]

def run(script, *arguments):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, arguments)], capture_output=True, text=True)

def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

class EndToEndTest(unittest.TestCase):
    def prepare(self, directory, project="A"):
        root = Path(directory) / f"project-{project.lower()}"
        shutil.copytree(FIXTURE, root)
        workspace = Path(directory) / "workspace"
        result = run("build_source_index.py", "--project", project, "--root", root, "--workspace", workspace)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = workspace / "indexes" / project / "source-index.jsonl"
        for file_name in MODULE_FILES:
            result = run("update_module_ownership.py", "--index", index, "--file", file_name, "--module", "product", "--role", "PRIMARY")
            self.assertEqual(result.returncode, 0, result.stderr)
        return root, workspace

    def analyze(self, root, workspace, project="A"):
        run_id = f"{project}-product-20260805-001"
        result = run("run_analysis.py", "--project", project, "--module", "product", "--root", root, "--sql-root", root / "database", "--workspace", workspace, "--analysis-run-id", run_id)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return run_id

    def test_fixture_pipeline_queries_lines_and_quality_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            run_id = self.analyze(root, workspace)
            api = jsonl(workspace / "indexes/A/api-index.jsonl")[0]
            for key in ("route_evidence", "controller_evidence", "validation_evidence", "service_evidence", "persistence_evidence", "side_effect_evidence"):
                self.assertTrue(api[key], key)
                for item in api[key]:
                    lines = (root / item["file"]).read_text(encoding="utf-8").splitlines()
                    self.assertLessEqual(item["start_line"], item["end_line"])
                    self.assertLessEqual(item["end_line"], len(lines))
            callers = run("query_indexes.py", "--project", "A", "--workspace", workspace, "--callers-of", r"App\Repositories\ProductRepository::create")
            self.assertEqual(callers.returncode, 0, callers.stderr)
            self.assertIn(r"App\\Services\\ProductService::create", callers.stdout)
            owner = run("query_indexes.py", "--project", "A", "--workspace", workspace, "--file", "app/Services/ProductService.php")
            self.assertIn('"module": "product"', owner.stdout)
            rule = run("query_indexes.py", "--project", "A", "--workspace", workspace, "--business-rule", "DRAFT")
            self.assertEqual(rule.returncode, 0, rule.stderr)
            self.assertIn("A-PRODUCT-API-001", rule.stdout)
            self.assertIn("products", rule.stdout)
            self.assertNotIn("product_skus", rule.stdout)
            gate = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertEqual(gate["gate_count"], 18)
            self.assertEqual(gate["status"], "PARTIAL")
            module = jsonl(workspace / "indexes/A/module-index.jsonl")[0]
            self.assertNotEqual(module["status"], "ANALYZED")
            record = json.loads((workspace / f"analysis-runs/A/{run_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(record["final_status"], "PARTIAL")
            self.assertEqual([stage["name"] for stage in record["stages"]], ["source_index", "symbol_index", "routes", "tables", "modules", "business", "quality_gates"])
            self.assertTrue(record["files_read"])
            self.assertTrue(record["files_scanned"])
            self.assertTrue(record["files_reused_without_content_read"])
            self.assertTrue(record["files_written"])
            validation = run("validate_indexes.py", "--workspace", workspace, "--project", "A")
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_stale_evidence_propagates_without_cross_project_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root_a, workspace = self.prepare(directory, "A")
            self.analyze(root_a, workspace, "A")
            root_b = Path(directory) / "project-b"
            shutil.copytree(FIXTURE, root_b)
            result = run("build_source_index.py", "--project", "B", "--root", root_b, "--workspace", workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            before_b = (workspace / "indexes/B/source-index.jsonl").read_bytes()
            target = root_a / "app/Repositories/ProductRepository.php"
            target.write_text(target.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")
            stale = run("detect_stale_references.py", "--workspace", workspace, "--project", "A")
            self.assertEqual(stale.returncode, 0, stale.stderr)
            report = json.loads((workspace / "reports/stale-references.json").read_text(encoding="utf-8"))
            self.assertIn("A-PRODUCT-API-001", report["affected_interfaces"])
            self.assertIn("A-PRODUCT-RULE-001", report["affected_rules"])
            api = jsonl(workspace / "indexes/A/api-index.jsonl")[0]
            self.assertEqual(api["status"], "REVIEW_REQUIRED")
            self.assertTrue(any(item.get("status") == "STALE" for item in api["persistence_evidence"]))
            module = jsonl(workspace / "indexes/A/module-index.jsonl")[0]
            self.assertEqual(module["status"], "REVIEW_REQUIRED")
            self.assertEqual(before_b, (workspace / "indexes/B/source-index.jsonl").read_bytes())

    def test_a_and_b_indexes_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root_a, workspace = self.prepare(directory, "A")
            root_b = Path(directory) / "project-b"
            shutil.copytree(FIXTURE, root_b)
            result = run("build_source_index.py", "--project", "B", "--root", root_b, "--workspace", workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows_a = jsonl(workspace / "indexes/A/source-index.jsonl")
            rows_b = jsonl(workspace / "indexes/B/source-index.jsonl")
            self.assertTrue(all(row["project"] == "A" and row["repository_root"] == str(root_a.resolve()) for row in rows_a))
            self.assertTrue(all(row["project"] == "B" and row["repository_root"] == str(root_b.resolve()) for row in rows_b))
            self.assertNotEqual({row["absolute_path"] for row in rows_a}, {row["absolute_path"] for row in rows_b})

    def test_business_refresh_preserves_other_modules_and_run_ids_are_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            index_dir = workspace / "indexes/A"
            (index_dir / "api-index.jsonl").write_text(json.dumps({"project": "A", "module": "orders", "api_id": "A-ORDERS-API-001"}) + "\n", encoding="utf-8")
            (index_dir / "business-index.jsonl").write_text(json.dumps({"project": "A", "module": "orders", "business_id": "A-ORDERS-RULE-001"}) + "\n", encoding="utf-8")
            run_id = self.analyze(root, workspace)
            self.assertTrue(any(row.get("module") == "orders" for row in jsonl(index_dir / "api-index.jsonl")))
            self.assertTrue(any(row.get("module") == "orders" for row in jsonl(index_dir / "business-index.jsonl")))
            duplicate = run("run_analysis.py", "--project", "A", "--module", "product", "--root", root, "--workspace", workspace, "--analysis-run-id", run_id)
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("already exists", duplicate.stderr)

if __name__ == "__main__":
    unittest.main()
