import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "sync.py"
SPEC = importlib.util.spec_from_file_location("sync_skills_catalog", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync)


class ContentHashTest(unittest.TestCase):
    def test_transient_files_do_not_change_content_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "sample-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: sample-skill\ndescription: sample\n---\n", encoding="utf-8")
            expected = sync.content_hash(skill)

            cache = skill / "scripts" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "worker.cpython-312.pyc").write_bytes(b"compiled")
            (skill / ".pytest_cache").mkdir()
            (skill / ".pytest_cache" / "state").write_text("state", encoding="utf-8")
            (skill / ".DS_Store").write_bytes(b"metadata")

            self.assertEqual(sync.content_hash(skill), expected)

    def test_real_source_change_changes_content_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "sample-skill"
            skill.mkdir()
            source = skill / "SKILL.md"
            source.write_text("version one\n", encoding="utf-8")
            before = sync.content_hash(skill)
            source.write_text("version two\n", encoding="utf-8")
            self.assertNotEqual(sync.content_hash(skill), before)


if __name__ == "__main__":
    unittest.main()
