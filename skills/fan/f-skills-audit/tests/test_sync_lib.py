import importlib.util
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "sync_lib.py"
SPEC = importlib.util.spec_from_file_location("sync_lib", LIB)
sync_lib = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_lib)


class ContentHashTest(unittest.TestCase):
    def test_ds_store_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            skill = Path(d) / "s"
            skill.mkdir()
            (skill / "SKILL.md").write_text("hello\n", encoding="utf-8")
            h1 = sync_lib.content_hash(skill)
            (skill / ".DS_Store").write_bytes(b"meta")
            self.assertEqual(sync_lib.content_hash(skill), h1)

    def test_content_change_changes_hash(self):
        with tempfile.TemporaryDirectory() as d:
            skill = Path(d) / "s"
            skill.mkdir()
            p = skill / "SKILL.md"
            p.write_text("v1\n", encoding="utf-8")
            before = sync_lib.content_hash(skill)
            p.write_text("v2\n", encoding="utf-8")
            self.assertNotEqual(sync_lib.content_hash(skill), before)


class AbsolutePathTest(unittest.TestCase):
    def test_detects_absolute(self):
        bad = {"targets": {"cursor": {"path": "/Users/x/.cursor/skills"}}}
        errs = sync_lib.find_absolute_paths(bad)
        self.assertTrue(errs)

    def test_allows_home_tilde(self):
        good = {"targets": {"cursor": {"path": "~/.cursor/skills"}}}
        self.assertEqual(sync_lib.find_absolute_paths(good), [])


class ProfileResolveTest(unittest.TestCase):
    def test_category_intersection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            agents = root / ".agents" / "skills"
            (agents / "a").mkdir(parents=True)
            (agents / "b").mkdir()
            catalog = {
                "skills": {
                    "a": {"categories": ["fan"]},
                    "b": {"categories": ["java"]},
                    "missing": {"categories": ["fan"]},
                }
            }
            cfg = {
                "profiles": {"default": {"include": {"categories": ["fan"], "names": []}}},
                "exclude": {"names": []},
            }
            names = sync_lib.resolve_profile(cfg, catalog, agents, "default")
            self.assertEqual(names, ["a"])


class AtomicCopyTest(unittest.TestCase):
    def test_copy_replaces_without_losing_on_success(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            dest = root / "dest"
            src.mkdir()
            (src / "SKILL.md").write_text("new\n", encoding="utf-8")
            dest.mkdir()
            (dest / "SKILL.md").write_text("old\n", encoding="utf-8")
            sync_lib.copy_skill_dir(src, dest)
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "new\n")


if __name__ == "__main__":
    unittest.main()
