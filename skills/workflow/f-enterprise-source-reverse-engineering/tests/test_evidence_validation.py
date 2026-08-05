import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL = Path(__file__).parents[1]; FIXTURE = SKILL / "tests/fixtures/mini-php-project"
class EvidenceTest(unittest.TestCase):
    def test_invalid_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "w"; subprocess.check_call([sys.executable, str(SKILL / "scripts/build_source_index.py"), "--project", "A", "--root", str(FIXTURE), "--workspace", str(workspace)])
            evidence = Path(directory) / "evidence.json"; evidence.write_text(json.dumps({"project":"B","file":"app/Services/ProductService.php","file_sha256":"0" * 64,"symbol":"ProductService","start_line":1,"end_line":2,"evidence_type":"implementation","confidence":"HIGH","analysis_run_id":"B-product-20260805-001"}))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/verify_source_evidence.py"), "--workspace", str(workspace), "--evidence", str(evidence)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0); self.assertIn("EVIDENCE_INVALID", result.stdout)
