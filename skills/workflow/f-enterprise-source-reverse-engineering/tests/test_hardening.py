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
from common import validation
from common.validation import REQUIRED_MODULE_DOCUMENTS


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, arguments)],
        capture_output=True,
        text=True,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class HardeningTest(unittest.TestCase):
    def prepare(self, directory):
        root = Path(directory) / "project-a"
        workspace = Path(directory) / "workspace"
        shutil.copytree(FIXTURE, root)
        result = run("build_source_index.py", "--project", "A", "--root", root, "--workspace", workspace)
        self.assertEqual(result.returncode, 0, result.stderr)
        source_path = workspace / "indexes/A/source-index.jsonl"
        for row in read_jsonl(source_path):
            result = run(
                "update_module_ownership.py", "--index", source_path,
                "--file", row["relative_path"], "--module", "product", "--role", "PRIMARY",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        return root, workspace

    def analyze(self, root, workspace):
        run_id = "A-product-20260805-001"
        result = run(
            "run_analysis.py", "--project", "A", "--module", "product",
            "--root", root, "--sql-root", root / "database",
            "--workspace", workspace, "--analysis-run-id", run_id,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return run_id

    def test_name_only_service_is_candidate_not_fact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project-a"
            shutil.copytree(FIXTURE, root)
            controller = root / "app/Http/Controllers/ProductController.php"
            text = controller.read_text(encoding="utf-8")
            text = text.replace(
                "use App\\Services\\ProductService;",
                "use App\\Services\\ProductService;\nuse App\\Services\\FakeService;",
            ).replace(
                "private ProductService $service) {}",
                "private ProductService $service, private FakeService $helper) {}",
            ).replace(
                "return $this->service->create($request->validated());",
                "$this->helper->touch();\n        return $this->service->create($request->validated());",
            )
            controller.write_text(text, encoding="utf-8")
            fake = root / "app/Services/FakeService.php"
            fake.write_text(
                "<?php\nnamespace App\\Services;\nclass FakeService {\n"
                "    public function touch(): bool { return true; }\n}\n",
                encoding="utf-8",
            )
            duplicate = root / "app/Other/ProductRequest.php"
            duplicate.parent.mkdir()
            duplicate.write_text(
                "<?php\nnamespace App\\Other;\nclass ProductRequest {\n"
                "    public function execute(): bool { return true; }\n}\n",
                encoding="utf-8",
            )
            workspace = Path(directory) / "workspace"
            result = run("build_source_index.py", "--project", "A", "--root", root, "--workspace", workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            source_path = workspace / "indexes/A/source-index.jsonl"
            for row in read_jsonl(source_path):
                result = run("update_module_ownership.py", "--index", source_path, "--file", row["relative_path"], "--module", "product", "--role", "PRIMARY")
                self.assertEqual(result.returncode, 0, result.stderr)
            self.analyze(root, workspace)
            api = read_jsonl(workspace / "indexes/A/api-index.jsonl")[0]
            self.assertIn("App\\Http\\Requests\\ProductRequest", {item["symbol"] for item in api["validation_evidence"]})
            candidate = next(item for item in api["candidates"] if item["symbol"] == "App\\Services\\FakeService::touch")
            self.assertEqual(candidate["role"], "service")
            self.assertEqual(candidate["confidence"], "MEDIUM")
            self.assertNotIn(
                "App\\Services\\FakeService::touch",
                {item["symbol"] for item in api["service_evidence"]},
            )
            self.assertEqual(api["status"], "PARTIAL")

    def test_reviewed_not_applicable_evidence_passes_and_plain_absence_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            run_id = self.analyze(root, workspace)
            api_path = workspace / "indexes/A/api-index.jsonl"
            api = read_jsonl(api_path)[0]
            reviewed = dict(api["controller_evidence"][0])
            reviewed["semantic_basis"] = "reviewed_negative_evidence"
            reviewed["reviewer"] = "AUDIT-001"
            reviewed["reviewed_at"] = "2026-08-05T00:00:00Z"
            api["coverage"]["transaction"] = {"status": "NOT_APPLICABLE", "rationale": "reviewed call chain has no transaction boundary"}
            api["coverage"]["side_effect"] = {"status": "NOT_APPLICABLE", "rationale": "reviewed call chain has no external side effect"}
            transaction_absence = dict(reviewed, evidence_type="transaction_absence")
            side_effect_absence = dict(reviewed, evidence_type="side_effect_absence")
            api["transaction_evidence"] = []
            api["side_effect_evidence"] = [side_effect_absence]
            write_jsonl(api_path, [api])

            business_path = workspace / "indexes/A/business-index.jsonl"
            business = read_jsonl(business_path)
            for number, kind in enumerate(("state_transition_absence", "concurrency_idempotency_absence", "cross_module_dependency_absence"), 1):
                business.append({
                    "project": "A", "module": "product", "business_id": f"A-ABSENCE-{number:03d}",
                    "type": kind, "name": kind, "classification": "FACT", "confidence": "HIGH",
                    "rationale": "reviewed reachable call graph and found this dimension not applicable",
                    "reviewer": "AUDIT-001", "reviewed_at": "2026-08-05T00:00:00Z",
                    "evidence": [dict(reviewed, evidence_type=kind)],
                    "related_apis": [api["api_id"]], "related_tables": api["tables"],
                    "analysis_run_id": run_id, "status": "PARTIAL",
                })
            write_jsonl(business_path, business)

            document_root = workspace / "reverse-docs/project-a/modules/product"
            document_root.mkdir(parents=True)
            for name in REQUIRED_MODULE_DOCUMENTS:
                (document_root / name).write_text(
                    f"# {name}\n\nFACT: reviewed against current A source hash, symbols, and line ranges.\n",
                    encoding="utf-8",
                )
            run_path = workspace / f"analysis-runs/A/{run_id}.json"
            record = json.loads(run_path.read_text(encoding="utf-8"))
            record["finished_at"] = None
            record["final_status"] = "RUNNING"
            record["stages"] = record["stages"][:-1]
            run_path.write_text(json.dumps(record), encoding="utf-8")

            gate_args = ("--project", "A", "--module", "product", "--analysis-run-id", run_id, "--workspace", workspace)
            rejected = run("evaluate_quality_gates.py", *gate_args)
            self.assertEqual(rejected.returncode, 2, rejected.stdout + rejected.stderr)
            rejected_report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertFalse(next(item["passed"] for item in rejected_report["gates"] if item["gate"] == "transactions"))

            api["transaction_evidence"] = [transaction_absence]
            write_jsonl(api_path, [api])
            accepted = run("evaluate_quality_gates.py", *gate_args)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            accepted_report = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertEqual(accepted_report["passed_count"], 18)

    def test_snapshot_token_rejects_mismatch_and_index_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            manifest_path = workspace / "indexes/A/index-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            mismatch = run(
                "detect_stale_references.py", "--workspace", workspace, "--project", "A",
                "--trust-source-index", "--source-snapshot-id", "0" * 64,
            )
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("snapshot ID", mismatch.stderr)

            source_path = workspace / "indexes/A/source-index.jsonl"
            source_path.write_text(source_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            tampered = run(
                "detect_stale_references.py", "--workspace", workspace, "--project", "A",
                "--trust-source-index", "--source-snapshot-id", manifest["snapshot_id"],
            )
            self.assertNotEqual(tampered.returncode, 0)
            self.assertIn("source index changed", tampered.stderr)

    def test_reviewed_absence_writer_adds_auditable_metadata_and_rejects_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            run_id = self.analyze(root, workspace)
            api_path = workspace / "indexes/A/api-index.jsonl"
            api = read_jsonl(api_path)[0]

            conflict = run(
                "record_reviewed_absence.py", "--project", "A", "--module", "product",
                "--api-id", api["api_id"], "--dimension", "transaction",
                "--rationale", "reviewed all reachable calls", "--reviewer", "AUDIT-002",
                "--reviewed-at", "2026-08-05T00:00:00Z",
                "--analysis-run-id", run_id, "--workspace", workspace,
            )
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn("PRESENT", conflict.stderr)

            api["coverage"]["transaction"] = {"status": "UNRESOLVED", "rationale": "requires review"}
            api["transaction_evidence"] = []
            write_jsonl(api_path, [api])
            for dimension in ("transaction", "state_transition"):
                result = run(
                    "record_reviewed_absence.py", "--project", "A", "--module", "product",
                    "--api-id", api["api_id"], "--dimension", dimension,
                    "--rationale", "reviewed the complete reachable call graph",
                    "--reviewer", "AUDIT-002", "--reviewed-at", "2026-08-05T00:00:00Z",
                    "--analysis-run-id", run_id, "--workspace", workspace,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            updated = read_jsonl(api_path)[0]
            absence = updated["transaction_evidence"][0]
            self.assertEqual(updated["coverage"]["transaction"]["status"], "NOT_APPLICABLE")
            self.assertEqual(absence["evidence_type"], "transaction_absence")
            self.assertEqual(absence["reviewer"], "AUDIT-002")
            business = read_jsonl(workspace / "indexes/A/business-index.jsonl")
            state_absence = next(row for row in business if row.get("type") == "state_transition_absence")
            self.assertEqual(state_absence["related_apis"], [api["api_id"]])
            self.assertEqual(state_absence["evidence"][0]["evidence_type"], "state_transition_absence")
            validated = run("validate_indexes.py", "--workspace", workspace, "--project", "A")
            self.assertEqual(validated.returncode, 0, validated.stderr + validated.stdout)

    def test_trusted_validation_reuses_snapshot_but_direct_validation_rehashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            self.analyze(root, workspace)
            manifest = json.loads((workspace / "indexes/A/index-manifest.json").read_text(encoding="utf-8"))

            with mock.patch.object(validation, "file_fingerprint", wraps=validation.file_fingerprint) as direct:
                self.assertEqual(validation.validate_project_indexes(workspace, "A"), [])
                self.assertGreaterEqual(direct.call_count, len(read_jsonl(workspace / "indexes/A/source-index.jsonl")))

            with mock.patch.object(validation, "file_fingerprint", wraps=validation.file_fingerprint) as trusted:
                self.assertEqual(validation.validate_project_indexes(
                    workspace, "A", trust_source_index=True,
                    source_snapshot_id=manifest["snapshot_id"],
                ), [])
                self.assertEqual(trusted.call_count, 0)

    def test_module_scoped_validation_is_not_overwritten_by_the_last_module_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            self.analyze(root, workspace)
            source_path = workspace / "indexes/A/source-index.jsonl"
            extra = run(
                "update_module_ownership.py", "--index", source_path,
                "--file", "app/Services/ProductService.php", "--module", "zzz",
                "--role", "SECONDARY",
            )
            self.assertEqual(extra.returncode, 0, extra.stderr)
            rebuilt = run("build_module_index.py", "--project", "A", "--workspace", workspace)
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            api_path = workspace / "indexes/A/api-index.jsonl"
            api = read_jsonl(api_path)[0]
            api["route_evidence"] = []
            write_jsonl(api_path, [api])
            errors = validation.validate_project_indexes(workspace, "A", "product")
            self.assertTrue(any(error.startswith("api-index.jsonl") for error in errors), errors)

    def test_finalize_rejects_source_changes_after_the_recorded_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace = self.prepare(directory)
            run_id = self.analyze(root, workspace)
            target = root / "app/Http/Controllers/ProductController.php"
            target.write_text(target.read_text(encoding="utf-8") + "\n// changed after review\n", encoding="utf-8")
            result = run(
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", root, "--sql-root", root / "database", "--workspace", workspace,
                "--analysis-run-id", run_id, "--finalize",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source changed since the recorded snapshot", result.stderr)
            record = json.loads((workspace / f"analysis-runs/A/{run_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(record["final_status"], "PARTIAL")
            self.assertEqual(record["finalization_count"], 0)

    def test_resume_starts_at_first_failed_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project-a"
            workspace = Path(directory) / "workspace"
            root.mkdir()
            manifest_path = workspace / "indexes/A/index-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps({
                "project": "A", "repository_root": str(root.resolve()), "snapshot_id": "a" * 64,
            }), encoding="utf-8")
            run_id = "A-product-20260805-001"
            argv = [
                "run_analysis.py", "--project", "A", "--module", "product",
                "--root", str(root), "--workspace", str(workspace),
                "--analysis-run-id", run_id,
            ]

            def record_files(record, *_args):
                record["files_scanned"] = [str(root / "source.php")]
                record["files_read"] = [str(manifest_path)]
                record["files_written"] = [str(workspace / "indexes/A/source-index.jsonl")]

            first_results = [
                subprocess.CompletedProcess([], 0, "source", ""),
                subprocess.CompletedProcess([], 0, "stale", ""),
                subprocess.CompletedProcess([], 0, "symbols", ""),
                subprocess.CompletedProcess([], 7, "", "route failure"),
            ]
            with mock.patch.object(run_analysis.subprocess, "run", side_effect=first_results), mock.patch.object(run_analysis, "refresh_file_record", side_effect=record_files), mock.patch.object(sys, "argv", argv):
                self.assertEqual(run_analysis.main(), 1)
            run_path = workspace / f"analysis-runs/A/{run_id}.json"
            failed = json.loads(run_path.read_text(encoding="utf-8"))
            self.assertEqual([stage["name"] for stage in failed["stages"]], ["source_index", "stale_references", "symbol_index", "routes"])
            self.assertEqual(failed["final_status"], "FAILED")

            report_path = workspace / "reports/A/product-quality-gates.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps({
                "project": "A", "module": "product", "analysis_run_id": run_id,
                "status": "PARTIAL", "gates": [{"gate": "documents", "passed": False}],
            }), encoding="utf-8")
            second_results = [
                subprocess.CompletedProcess([], 0, "routes", ""),
                subprocess.CompletedProcess([], 0, "tables", ""),
                subprocess.CompletedProcess([], 0, "modules", ""),
                subprocess.CompletedProcess([], 0, "business", ""),
                subprocess.CompletedProcess([], 2, "partial", ""),
            ]
            resumed_argv = argv + ["--resume"]
            with mock.patch.object(run_analysis.subprocess, "run", side_effect=second_results) as resumed, mock.patch.object(run_analysis, "refresh_file_record", side_effect=record_files), mock.patch.object(run_analysis, "continuation_source_errors", return_value=[]), mock.patch.object(sys, "argv", resumed_argv):
                self.assertEqual(run_analysis.main(), 0)
            scripts = [Path(call.args[0][1]).name for call in resumed.call_args_list]
            self.assertEqual(scripts, ["extract_php_routes.py", "extract_sql_tables.py", "build_module_index.py", "build_business_index.py", "evaluate_quality_gates.py"])
            completed = json.loads(run_path.read_text(encoding="utf-8"))
            self.assertEqual(completed["resume_count"], 1)
            self.assertEqual(len(completed["resumed_at"]), 1)
            self.assertEqual(completed["final_status"], "PARTIAL")
            self.assertEqual(len(completed["stages"]), 8)


if __name__ == "__main__":
    unittest.main()
