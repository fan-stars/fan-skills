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

            subprocess.check_call([sys.executable, str(SKILL / "scripts/build_module_index.py"), "--project", "A", "--workspace", str(workspace)])
            module_index = workspace / "indexes/A/module-index.jsonl"
            modules = [json.loads(line) for line in module_index.read_text().splitlines()]
            for module in modules:
                module["status"] = "ANALYZED"
                module["quality_gates"] = [{"gate": "sentinel", "passed": True}]
            module_index.write_text("".join(json.dumps(module) + "\n" for module in modules), encoding="utf-8")
            subprocess.check_call([sys.executable, str(SKILL / "scripts/build_module_index.py"), "--project", "A", "--workspace", str(workspace)])
            rebuilt = [json.loads(line) for line in module_index.read_text().splitlines()]
            self.assertTrue(all(module["status"] == "ANALYZED" for module in rebuilt))
            self.assertTrue(all(module["quality_gates"] == [{"gate": "sentinel", "passed": True}] for module in rebuilt))

            lock = index.with_name(f".{index.name}.lock")
            lock.write_text('{"pid": 2147483647, "token": "dead", "created_at": 0}', encoding="ascii")
            recovered = subprocess.run([sys.executable, str(SKILL / "scripts/update_module_ownership.py"), "--index", str(index), "--file", file_name, "--module", "catalog", "--role", "SHARED"], capture_output=True, text=True)
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertFalse(lock.exists())
