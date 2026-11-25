import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillDocTest(unittest.TestCase):
    def test_parent_menu_and_dict_rules_are_written(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        prompts = (ROOT / "prompts.md").read_text(encoding="utf-8")
        reference = (ROOT / "reference.md").read_text(encoding="utf-8")
        self.assertIn("parentMenuId", skill)
        self.assertIn("固定传 `0`", skill)
        self.assertIn("common_", skill)
        self.assertIn("是否", prompts)
        self.assertIn("common_status", prompts)
        self.assertIn("Integer", prompts)
        self.assertIn("parentMenuId", reference)
        self.assertIn("只用来通过远端校验", reference)
        self.assertNotIn("infra_boolean_string", prompts)
