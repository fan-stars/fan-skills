import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

SKILL = Path(__file__).parents[1]

class SkillHygieneTest(unittest.TestCase):
    def test_frontmatter_utf8_no_bom_or_leading_blank_and_name_matches_folder(self):
        data = (SKILL / "SKILL.md").read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(data.startswith(b"---\n"))
        text = data.decode("utf-8")
        metadata = yaml.safe_load(text.split("---\n", 2)[1])
        self.assertEqual(set(metadata), {"name", "description"})
        self.assertEqual(metadata["name"], SKILL.name)
        self.assertTrue(metadata["description"].strip())
        interface = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))["interface"]
        self.assertIn(f"${SKILL.name}", interface["default_prompt"])

    def test_no_empty_or_placeholder_files(self):
        files = [path for path in SKILL.rglob("*") if path.is_file()]
        self.assertTrue(files)
        self.assertFalse([path for path in files if not path.read_bytes()])
        pattern = re.compile(r"\b(?:TODO|TBD|FIXME|not implemented)\b|待实现|待补充", re.I)
        offenders = []
        for path in files:
            if path == Path(__file__):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if pattern.search(text):
                offenders.append(path)
        self.assertFalse(offenders)

    def test_documented_scripts_exist_and_all_scripts_support_help(self):
        docs = (SKILL / "SKILL.md").read_text(encoding="utf-8") + (SKILL / "README.md").read_text(encoding="utf-8")
        names = set(re.findall(r"(?:scripts/)?([a-z][a-z0-9_]+\.py)", docs))
        self.assertFalse([name for name in names if name != "quick_validate.py" and not (SKILL / "scripts" / name).is_file()])
        for path in (SKILL / "scripts").glob("*.py"):
            result = subprocess.run([sys.executable, str(path), "--help"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"{path}: {result.stderr}")

    def test_scripts_avoid_posix_only_apis(self):
        source = "\n".join(path.read_text(encoding="utf-8") for path in (SKILL / "scripts").rglob("*.py"))
        for token in ("import fcntl", "import pwd", "os.fork(", "/bin/bash", "os.system("):
            self.assertNotIn(token, source)

    def test_fixture_example_runs(self):
        result = subprocess.run([sys.executable, str(SKILL / "scripts/run_fixture_example.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = __import__("json").loads(result.stdout)
        self.assertTrue(output["callers"])
        self.assertTrue(output["rules"])
        self.assertEqual(output["quality_gate"]["total"], 18)

    def test_document_validation_rejects_missing_module_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([
                sys.executable, str(SKILL / "scripts/validate_documents.py"),
                "--workspace", directory, "--project", "A", "--module", "product",
            ], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required module document", result.stdout)

if __name__ == "__main__":
    unittest.main()
