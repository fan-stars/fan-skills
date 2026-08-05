import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL = Path(__file__).parents[1]; FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class SymbolTest(unittest.TestCase):
    def test_symbols_have_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "w"
            subprocess.check_call([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)])
            result = subprocess.run([sys.executable, str(SKILL / "scripts/build_symbol_index.py"), "--project", "A", "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in (workspace / "indexes/A/symbol-index.jsonl").read_text().splitlines()]
            self.assertTrue(any(row["name"] == "ProductService" and row["start_line"] <= row["end_line"] for row in rows))
            repository = next(row for row in rows if row["fully_qualified_name"] == r"App\Repositories\ProductRepository::create")
            self.assertIn(r"App\Services\ProductService::create", repository["called_by"])
            controller = next(row for row in rows if row["fully_qualified_name"] == r"App\Http\Controllers\ProductController::store")
            self.assertEqual(controller["parameter_types"], [r"App\Http\Requests\ProductRequest"])
            second = subprocess.run([sys.executable, str(SKILL / "scripts/build_symbol_index.py"), "--project", "A", "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("parsed=0", second.stdout)
            manifest_path = workspace / "indexes/A/symbol-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["parser_version"] = 1
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            upgraded = subprocess.run([sys.executable, str(SKILL / "scripts/build_symbol_index.py"), "--project", "A", "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
            self.assertNotIn("parsed=0", upgraded.stdout)
