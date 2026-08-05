import hashlib, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

SKILL = Path(__file__).parents[1]
FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class SourceIndexTest(unittest.TestCase):
    def test_index_hash_and_line_count(self):
        before = {path.relative_to(FIXTURE): hashlib.sha256(path.read_bytes()).hexdigest() for path in FIXTURE.rglob("*") if path.is_file()}
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            result = subprocess.run([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in (workspace / "indexes/A/source-index.jsonl").read_text().splitlines()]
            service = next(row for row in rows if row["relative_path"].endswith("ProductService.php"))
            self.assertGreater(service["line_count"], 1)
            self.assertEqual(len(service["sha256"]), 64)
        after = {path.relative_to(FIXTURE): hashlib.sha256(path.read_bytes()).hexdigest() for path in FIXTURE.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_workspace_inside_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            shutil.copytree(FIXTURE, root)
            result = subprocess.run(
                [sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(root), "--workspace", str(root / "reverse-workspace")],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside analyzed source root", result.stderr)

    def test_unchanged_files_are_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            command = [sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)]
            self.assertEqual(subprocess.run(command, capture_output=True, text=True).returncode, 0)
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            manifest = json.loads((workspace / "indexes/A/index-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["changed_or_deleted"], 0)
            self.assertEqual(manifest["unchanged_reused"], manifest["file_count"])
