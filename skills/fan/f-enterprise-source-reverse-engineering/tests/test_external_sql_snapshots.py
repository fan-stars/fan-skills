import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1]
SCRIPTS = SKILL / "scripts"
FIXTURE = SKILL / "tests/fixtures/mini-php-project"
sys.path.insert(0, str(SCRIPTS))
from common import validation


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, arguments)],
        capture_output=True,
        text=True,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


class ExternalSqlSnapshotTest(unittest.TestCase):
    def prepare(self, directory):
        base = Path(directory)
        root = base / "project-a"
        workspace = base / "workspace"
        shutil.copytree(FIXTURE, root)
        sql_file = workspace / "authoritative-sql" / "schema.sql"
        sql_file.parent.mkdir(parents=True)
        sql_file.write_text(
            "-- authoritative production snapshot\n"
            "CREATE TABLE `products` (\n"
            "  `id` bigint primary key\n"
            ");\n",
            encoding="utf-8",
        )
        source = run("build_source_index.py", "--project", "A", "--root", root, "--workspace", workspace)
        self.assertEqual(source.returncode, 0, source.stderr)
        source_path = workspace / "indexes/A/source-index.jsonl"
        for row in read_jsonl(source_path):
            result = run(
                "update_module_ownership.py", "--index", source_path,
                "--file", row["relative_path"], "--module", "product", "--role", "PRIMARY",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        run_id = "A-product-20260806-001"
        analyzed = run(
            "run_analysis.py", "--project", "A", "--module", "product",
            "--root", root, "--sql-root", sql_file,
            "--workspace", workspace, "--analysis-run-id", run_id,
        )
        self.assertEqual(analyzed.returncode, 0, analyzed.stdout + analyzed.stderr)
        return root, workspace, sql_file, run_id

    def test_external_snapshot_generation_and_authenticity_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            _, workspace, sql_file, run_id = self.prepare(directory)
            table_path = workspace / "indexes/A/table-index.jsonl"
            rows = read_jsonl(table_path)
            self.assertEqual(len(rows), 1)
            original = rows[0]
            self.assertEqual(original["file"], "authoritative-sql/schema.sql")
            self.assertEqual(original["source_scope"], validation.EXTERNAL_SQL_SNAPSHOT)
            self.assertEqual(original["start_line"], 2)

            gate = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            current = next(item for item in gate["gates"] if item["gate"] == "current_evidence")
            self.assertTrue(current["passed"], gate["validation_errors"])
            self.assertFalse(any("project or source linkage mismatch" in error for error in gate["validation_errors"]))
            self.assertEqual(validation.validate_project_indexes(workspace, "A"), [])
            run_record = json.loads((workspace / f"analysis-runs/A/{run_id}.json").read_text(encoding="utf-8"))
            self.assertIn(str(sql_file.resolve()), run_record["files_scanned"])
            self.assertIn(str(sql_file.resolve()), run_record["files_read"])
            self.assertNotIn(str((Path(run_record["source_root"]) / original["file"]).resolve()), run_record["files_read"])

            second = run(
                "extract_sql_tables.py", "--project", "A", "--root", sql_file,
                "--workspace", workspace,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("parsed=0 reused=1", second.stdout)

            legacy = dict(original)
            legacy.pop("source_scope")
            write_jsonl(table_path, [legacy])
            self.assertEqual(validation.validate_project_indexes(workspace, "A"), [])

            absolute = dict(original, file=str(sql_file.resolve()))
            write_jsonl(table_path, [absolute])
            self.assertEqual(validation.validate_project_indexes(workspace, "A"), [])

            wrong_hash = dict(original, file_sha256="0" * 64)
            write_jsonl(table_path, [wrong_hash])
            self.assertTrue(any("external SQL SHA-256 mismatch" in error for error in validation.validate_project_indexes(workspace, "A")))

            bad_lines = dict(original, end_line=999)
            write_jsonl(table_path, [bad_lines])
            self.assertTrue(any("external SQL line range is invalid" in error for error in validation.validate_project_indexes(workspace, "A")))

            missing = dict(original, file="authoritative-sql/missing.sql")
            write_jsonl(table_path, [missing])
            self.assertTrue(any("external SQL file is missing" in error for error in validation.validate_project_indexes(workspace, "A")))

            escaping = dict(original, file="../outside.sql")
            write_jsonl(table_path, [escaping])
            self.assertTrue(any("escapes workspace" in error for error in validation.validate_project_indexes(workspace, "A")))

            project_scoped = dict(original, source_scope=validation.PROJECT_SOURCE)
            write_jsonl(table_path, [project_scoped])
            self.assertTrue(any("project or source linkage mismatch" in error for error in validation.validate_project_indexes(workspace, "A")))

            write_jsonl(table_path, [original])
            finalized = run(
                "evaluate_quality_gates.py", "--project", "A", "--module", "product",
                "--analysis-run-id", run_id, "--workspace", workspace,
            )
            self.assertEqual(finalized.returncode, 2, finalized.stdout + finalized.stderr)
            refreshed_gate = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
            self.assertTrue(next(item for item in refreshed_gate["gates"] if item["gate"] == "current_evidence")["passed"])

    def test_external_sql_outside_workspace_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "project-a"
            workspace = base / "workspace"
            shutil.copytree(FIXTURE, root)
            source = run("build_source_index.py", "--project", "A", "--root", root, "--workspace", workspace)
            self.assertEqual(source.returncode, 0, source.stderr)
            outside = base / "outside.sql"
            outside.write_text("CREATE TABLE outside_table (id int);\n", encoding="utf-8")
            result = run(
                "extract_sql_tables.py", "--project", "A", "--root", outside,
                "--workspace", workspace,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external SQL root must be inside the analysis workspace", result.stderr)


if __name__ == "__main__":
    unittest.main()
