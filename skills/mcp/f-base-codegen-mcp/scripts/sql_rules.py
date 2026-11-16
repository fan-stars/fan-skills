from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

BLOCK_RE = re.compile(
    r"<!--\s*sql-id-segments:start\s*-->\s*```json\s*(.*?)\s*```\s*"
    r"<!--\s*sql-id-segments:end\s*-->", re.S)
RUNTIME_START = 100001


def _as_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def load_rules(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"missing rules file: {path}")
    return load_rules_from_text(path.read_text(encoding="utf-8"))


def load_rules_from_text(text: str) -> dict:
    match = BLOCK_RE.search(text)
    if not match:
        raise ValueError("sql-id-segments block not found")
    try:
        rules = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid rules json: {error}") from error
    if not isinstance(rules, dict):
        raise ValueError("rules json must be an object")
    for key in ("modules", "nextModuleBase", "autoIncrement"):
        if key not in rules:
            raise ValueError(f"missing rules key: {key}")
    modules = rules["modules"]
    if not isinstance(modules, dict):
        raise ValueError("modules must be an object")
    for name, value in modules.items():
        _as_int(value, f"modules.{name}")
    auto = rules["autoIncrement"]
    if not isinstance(auto, dict):
        raise ValueError("autoIncrement must be an object")
    if "default" not in auto or "shared" not in auto:
        raise ValueError("missing autoIncrement keys")
    _as_int(auto["default"], "autoIncrement.default")
    shared = auto["shared"]
    if not isinstance(shared, dict):
        raise ValueError("autoIncrement.shared must be an object")
    for name, value in shared.items():
        _as_int(value, f"autoIncrement.shared.{name}")
    next_base = _as_int(rules["nextModuleBase"], "nextModuleBase")
    if next_base <= 0 or next_base >= RUNTIME_START:
        raise ValueError("nextModuleBase must be in (0, 100001)")
    return rules


def segment_bounds(rules: dict, module: str) -> tuple[int, int]:
    modules = {name: int(value) for name, value in rules["modules"].items()}
    if module not in modules:
        raise ValueError(f"module not registered: {module}")
    base = modules[module]
    if base <= 0 or base >= RUNTIME_START:
        raise ValueError(f"module base out of range: {base}")
    upper = min([value for value in modules.values() if value > base]
                + [int(rules["nextModuleBase"])])
    if upper <= base:
        raise ValueError(f"invalid segment: [{base}, {upper})")
    return base, upper


def next_id_in_segment(ids: Iterable[int], base: int, upper: int) -> int:
    if upper <= base:
        raise ValueError(f"invalid segment: [{base}, {upper})")
    used = [int(value) for value in ids if base <= int(value) < upper]
    candidate = max(used) + 1 if used else base
    if candidate >= upper:
        raise ValueError(f"segment exhausted: [{base}, {upper})")
    return candidate
