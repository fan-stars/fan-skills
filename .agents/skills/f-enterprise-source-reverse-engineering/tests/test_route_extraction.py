import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL = Path(__file__).parents[1]; FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class RouteTest(unittest.TestCase):
    def test_route_is_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            indexed = subprocess.run([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            result = subprocess.run([sys.executable, str(SKILL / "scripts/extract_php_routes.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            row = json.loads((workspace / "indexes/A/routes.jsonl").read_text().splitlines()[0]); self.assertEqual(row["path"], "/api/products"); self.assertEqual(row["classification"], "CANDIDATE"); self.assertEqual(row["project"], "A")
            second = subprocess.run([sys.executable, str(SKILL / "scripts/extract_php_routes.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)], capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr); self.assertIn("parsed=0", second.stdout)
