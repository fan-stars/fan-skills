import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sql_rules import load_rules, load_rules_from_text, next_id_in_segment, segment_bounds

RULES = """<!-- sql-id-segments:start -->
```json
{"nextModuleBase": 3001, "modules": {"system": 1, "infra": 2001},
 "autoIncrement": {"default": 10001, "shared": {"system_menu": 100001}}}
```
<!-- sql-id-segments:end -->"""


class TestSqlRules(unittest.TestCase):
    def test_loads_bounds(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text(RULES, encoding="utf-8")
            rules = load_rules(path)
        self.assertEqual(segment_bounds(rules, "system"), (1, 2001))
        self.assertEqual(segment_bounds(rules, "infra"), (2001, 3001))

    def test_unregistered_module_stops(self) -> None:
        rules = load_rules_from_text(RULES)
        with self.assertRaises(ValueError):
            segment_bounds(rules, "pay")

    def test_next_id_ignores_out_of_segment(self) -> None:
        self.assertEqual(next_id_in_segment([1, 124, 13480], 1, 2001), 125)
        self.assertEqual(next_id_in_segment([2001, 2054], 2001, 3001), 2055)

    def test_exhausted_segment_stops(self) -> None:
        with self.assertRaises(ValueError):
            next_id_in_segment([2000], 1, 2001)

    def test_malformed_rules_stops(self) -> None:
        with self.assertRaises(ValueError):
            load_rules_from_text("no block")

    def test_runtime_boundary_stops(self) -> None:
        with self.assertRaises(ValueError):
            load_rules_from_text(RULES.replace('"nextModuleBase": 3001',
                                               '"nextModuleBase": 100001'))

    def test_invalid_json_stops(self) -> None:
        text = RULES.replace('{"nextModuleBase"', '{not json "nextModuleBase"')
        with self.assertRaises(ValueError):
            load_rules_from_text(text)

    def test_missing_key_stops(self) -> None:
        with self.assertRaises(ValueError):
            load_rules_from_text(RULES.replace('"modules": {"system": 1, "infra": 2001},', ""))

    def test_non_object_modules_stops(self) -> None:
        with self.assertRaises(ValueError):
            load_rules_from_text(RULES.replace('{"system": 1, "infra": 2001}', "[]"))

    def test_non_integer_next_module_base_stops(self) -> None:
        for value in ("null", "100002", "-1", "true"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    load_rules_from_text(RULES.replace('"nextModuleBase": 3001',
                                                       f'"nextModuleBase": {value}'))

    def test_inverted_segment_stops(self) -> None:
        rules = load_rules_from_text(RULES.replace('"system": 1', '"system": 5000'))
        with self.assertRaises(ValueError):
            segment_bounds(rules, "system")

    def test_base_out_of_range_stops(self) -> None:
        rules = load_rules_from_text(RULES.replace('"system": 1', '"system": 200000'))
        with self.assertRaises(ValueError):
            segment_bounds(rules, "system")

    def test_empty_and_invalid_segment(self) -> None:
        self.assertEqual(next_id_in_segment([], 1, 2001), 1)
        with self.assertRaises(ValueError):
            next_id_in_segment([], 2001, 2001)

    def test_missing_file_stops(self) -> None:
        with self.assertRaises(ValueError):
            load_rules(Path("/nonexistent/rules.md"))
