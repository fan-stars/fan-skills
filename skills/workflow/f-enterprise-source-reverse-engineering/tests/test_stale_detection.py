import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL = Path(__file__).parents[1]; FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class StaleTest(unittest.TestCase):
    def test_changed_file_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"; shutil.copytree(FIXTURE, root); workspace = Path(directory) / "w"
            subprocess.check_call([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(root), "--workspace", str(workspace)])
            target = root / "app/Models/Product.php"; target.write_text(target.read_text() + "\n// changed\n")
            result = subprocess.run([sys.executable, str(SKILL / "scripts/detect_stale_references.py"), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0); report = json.loads((workspace / "reports/stale-references.json").read_text()); self.assertTrue(any(item["file"].endswith("Product.php") for item in report["items"]))
