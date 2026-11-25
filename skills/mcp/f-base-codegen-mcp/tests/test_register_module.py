import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import sql_rules

_FENCE = "`" * 3
README = (
    "| mcp | [3001, 4001) | 3007 | 3003 | 3018 | 3001 |\n"
    "| 下一个新模块 | [4001, 5001) | 4001 | 4001 | 4001 | 4001 |\n"
    "\n"
    "<!-- sql-id-segments:start -->\n"
    + _FENCE + "json\n"
    + "{\n"
    + '  "nextModuleBase": 4001,\n'
    + '  "modules": {"system": 1, "infra": 2001, "mcp": 3001},\n'
    + '  "autoIncrement": {"default": 10001, "shared": {"system_menu": 100001}}\n'
    + "}\n"
    + _FENCE + "\n"
    + "<!-- sql-id-segments:end -->\n"
)

JAVA = """public class ServiceErrorCodeRange {

    // 模块 infra 错误码区间 [1-001-000-000 ~ 1-002-000-000)
    // 模块 system 错误码区间 [1-002-000-000 ~ 1-003-000-000)
    // 模块 mcp 错误码区间 [1-003-000-000 ~ 1-004-000-000)

}
"""


class TestRegisterModule(unittest.TestCase):
    def test_apply_appends_module_and_second_run_errors(self) -> None:
        from scripts.register_module import register_module, RegisterError
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            java = root / "ServiceErrorCodeRange.java"
            readme.write_text(README, encoding="utf-8")
            java.write_text(JAVA, encoding="utf-8")
            diff = register_module(readme, java, "shop", apply=False)
            self.assertIn("shop", diff)
            self.assertEqual(README, readme.read_text(encoding="utf-8"))
            register_module(readme, java, "shop", apply=True)
            text = readme.read_text(encoding="utf-8")
            rules = sql_rules.load_rules_from_text(text)
            self.assertEqual(4001, rules["modules"]["shop"])
            self.assertEqual(5001, rules["nextModuleBase"])
            self.assertIn("| shop | [4001, 5001) | 4001 | 4001 | 4001 | 4001 |", text)
            self.assertIn("| 下一个新模块 | [5001, 6001) | 5001 | 5001 | 5001 | 5001 |", text)
            java_text = java.read_text(encoding="utf-8")
            self.assertIn("// 模块 shop 错误码区间 [1-004-000-000 ~ 1-005-000-000)", java_text)
            self.assertLess(
                java_text.index("模块 mcp"),
                java_text.index("模块 shop"))
            with self.assertRaises(RegisterError):
                register_module(readme, java, "shop", apply=True)
            self.assertEqual(text, readme.read_text(encoding="utf-8"))
            self.assertEqual(java_text, java.read_text(encoding="utf-8"))

    def test_java_write_failure_restores_readme(self) -> None:
        from scripts.register_module import register_module
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            java = root / "missing" / "ServiceErrorCodeRange.java"
            readme.write_text(README, encoding="utf-8")
            with self.assertRaises(OSError):
                register_module(readme, java, "shop", apply=True)
            self.assertEqual(README, readme.read_text(encoding="utf-8"))
