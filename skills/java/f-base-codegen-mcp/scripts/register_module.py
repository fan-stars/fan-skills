"""登记新业务模块号段到 SQL README 与 ServiceErrorCodeRange。"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

try:
    from scripts.sql_rules import BLOCK_RE, RUNTIME_START, load_rules_from_text
except ModuleNotFoundError:  # 直接运行脚本时，脚本目录在 sys.path 上
    from sql_rules import BLOCK_RE, RUNTIME_START, load_rules_from_text

MODULE_NAME_RE = re.compile(r"^[a-z][a-z0-9]{0,29}$")
ERROR_CODE_RE = re.compile(
    r"// 模块\s+(\w+)\s+错误码区间\s+\[(\d+(?:-\d+)+)\s*~\s*(\d+(?:-\d+)+)\)"
)
NEXT_MODULE_ROW_RE = re.compile(
    r"\| 下一个新模块 \| \[\d+, \d+\) \| \d+ \| \d+ \| \d+ \| \d+ \|"
)


class RegisterError(Exception):
    """模块登记失败。"""


def _parse_error_code(text: str) -> int:
    return int(text.replace("-", ""))


def _format_error_code(value: int) -> str:
    digits = f"{value:010d}"
    return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:10]}"


def _unified_diff(path: Path, old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
    )


def _update_readme(text: str, module: str) -> str:
    rules = load_rules_from_text(text)
    modules = {name: int(value) for name, value in rules["modules"].items()}
    if module in modules:
        raise RegisterError(f"module already registered: {module}")
    base = int(rules["nextModuleBase"])
    next_base = base + 1000
    if next_base >= RUNTIME_START:
        raise RegisterError(f"nextModuleBase exhausted: {next_base}")
    if not NEXT_MODULE_ROW_RE.search(text):
        raise RegisterError("missing 下一个新模块 row")
    modules[module] = base
    rules["modules"] = modules
    rules["nextModuleBase"] = next_base
    modules_json = json.dumps(modules, ensure_ascii=False, indent=2).replace(
        "\n", "\n  ")
    auto_json = json.dumps(rules["autoIncrement"], ensure_ascii=False, indent=2).replace(
        "\n", "\n  ")
    json_body = (
        "{\n"
        f'  "nextModuleBase": {next_base},\n'
        f'  "modules": {modules_json},\n'
        f'  "autoIncrement": {auto_json}\n'
        "}"
    )

    def replace_block(match: re.Match[str]) -> str:
        return (
            f"{match.group(0)[:match.start(1) - match.start(0)]}"
            f"{json_body}"
            f"{match.group(0)[match.end(1) - match.start(0):]}"
        )

    updated = BLOCK_RE.sub(replace_block, text, count=1)
    module_row = (
        f"| {module} | [{base}, {next_base}) | {base} | {base} | {base} | {base} |"
    )
    next_row = (
        f"| 下一个新模块 | [{next_base}, {next_base + 1000}) | "
        f"{next_base} | {next_base} | {next_base} | {next_base} |"
    )
    updated = NEXT_MODULE_ROW_RE.sub(f"{module_row}\n{next_row}", updated, count=1)
    return updated


def _update_java(text: str, module: str) -> str:
    matches = list(ERROR_CODE_RE.finditer(text))
    if not matches:
        raise RegisterError("no error-code range comments found")
    for match in matches:
        if match.group(1) == module:
            raise RegisterError(f"module already in error-code comments: {module}")
    ranges: list[tuple[int, int]] = []
    for match in matches:
        start = _parse_error_code(match.group(2))
        end = _parse_error_code(match.group(3))
        ranges.append((start, end))
    new_start = max(end for _, end in ranges)
    new_end = new_start + 1_000_000
    for start, end in ranges:
        if new_start < end and new_end > start:
            raise RegisterError(
                f"error-code range overlaps: [{new_start}, {new_end})"
            )
    last = matches[-1]
    line_start = text.rfind("\n", 0, last.start()) + 1
    indent = text[line_start:last.start()]
    comment = (
        f"{indent}// 模块 {module} 错误码区间 "
        f"[{_format_error_code(new_start)} ~ {_format_error_code(new_end)})"
    )
    insert_at = text.find("\n", last.end())
    if insert_at == -1:
        return text + "\n" + comment
    return text[:insert_at] + "\n" + comment + text[insert_at:]


def register_module(readme: Path, java: Path, module: str, *, apply: bool) -> str:
    """在当前工作区登记号段；不绑定具体分支名，号段由各线自行维护。"""
    if not MODULE_NAME_RE.fullmatch(module):
        raise RegisterError(f"invalid module name: {module}")
    old_readme = readme.read_text(encoding="utf-8")
    new_readme = _update_readme(old_readme, module)
    if not apply:
        old_java = java.read_text(encoding="utf-8")
        new_java = _update_java(old_java, module)
        return _unified_diff(readme, old_readme, new_readme) + _unified_diff(
            java, old_java, new_java
        )
    readme_bytes = readme.read_bytes()
    readme.write_text(new_readme, encoding="utf-8")
    try:
        old_java = java.read_text(encoding="utf-8")
        new_java = _update_java(old_java, module)
        java.write_text(new_java, encoding="utf-8")
    except Exception:
        readme.write_bytes(readme_bytes)
        raise
    return _unified_diff(readme, old_readme, new_readme) + _unified_diff(
        java, old_java, new_java
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register a new module id segment")
    parser.add_argument("--module", required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = register_module(
            args.readme, args.java, args.module, apply=args.apply
        )
    except RegisterError as error:
        print(str(error), file=sys.stderr)
        return 2
    if not args.apply:
        print(result, end="" if result.endswith("\n") or not result else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
