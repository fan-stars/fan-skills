import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL = Path(__file__).parents[1]; FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class OwnershipTest(unittest.TestCase):
    def test_labels_append(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "w"; subprocess.check_call([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)])
            index = workspace / "indexes/A/source-index.jsonl"; file_name = "app/Services/ProductService.php"
            for module, role in (("product", "PRIMARY"), ("inventory", "SECONDARY")):
                subprocess.check_call([sys.executable, str(SKILL / "scripts/update_module_ownership.py"), "--index", str(index), "--file", file_name, "--module", module, "--role", role])
            row = next(json.loads(line) for line in index.read_text().splitlines() if json.loads(line)["relative_path"] == file_name)
            self.assertEqual({item["module"] for item in row["modules"]}, {"product", "inventory"})
