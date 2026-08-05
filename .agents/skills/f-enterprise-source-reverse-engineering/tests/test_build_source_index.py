import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
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

    def test_same_repository_root_cannot_be_bound_to_both_projects(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            command = [sys.executable, str(SKILL / "scripts/build_source_index.py")]
            first = subprocess.run(command + ["--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(command + ["--project", "B", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already bound", second.stderr)

    def test_verify_all_detects_same_size_change_with_preserved_mtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            workspace = Path(directory) / "workspace"
            shutil.copytree(FIXTURE, root)
            command = [sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(root), "--workspace", str(workspace)]
            self.assertEqual(subprocess.run(command, capture_output=True, text=True).returncode, 0)
            target = root / "app/Models/Product.php"
            original = target.read_bytes()
            before = target.stat()
            changed = original.replace(b"Product", b"Catalog", 1)
            self.assertEqual(len(original), len(changed))
            target.write_bytes(changed)
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
            incremental = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(incremental.returncode, 0, incremental.stderr)
            self.assertEqual(json.loads((workspace / "indexes/A/index-manifest.json").read_text())["changed_or_deleted"], 0)
            verified = subprocess.run(command + ["--verify-all"], capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            rows = [json.loads(line) for line in (workspace / "indexes/A/source-index.jsonl").read_text().splitlines()]
            model = next(row for row in rows if row["relative_path"] == "app/Models/Product.php")
            self.assertEqual(model["analysis_status"], "STALE")
            self.assertNotEqual(model["sha256"], hashlib.sha256(original).hexdigest())
