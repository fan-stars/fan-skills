"""把远程 MCP 代码生成 ZIP 落到本地仓库的辅助脚本。"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

try:
    from scripts.project_config import (
        ConfigError,
        ProjectConfig,
        enum_reference,
        load_project_config,
    )
    from scripts.sql_rules import load_rules, next_id_in_segment, segment_bounds
except ModuleNotFoundError:  # 直接运行脚本时，脚本目录在 sys.path 上
    from project_config import (
        ConfigError,
        ProjectConfig,
        enum_reference,
        load_project_config,
    )
    from sql_rules import load_rules, next_id_in_segment, segment_bounds

TABLE_MARKER = re.compile(r"-- Table structure for (\w+)")
ERROR_CODE = re.compile(
    r"ErrorCode\s+(\w+)\s*=\s*new ErrorCode\(TODO[^,]*,\s*\"([^\"]*)\"\);"
)


def map_frontend_path(logical: str, front_type: int, config: ProjectConfig) -> Path:
    """把清单里的前端逻辑路径映射到 Vben 子应用。"""
    if not logical.startswith(config.frontend_path_prefix):
        raise ValueError(f"frontend path does not match prefix: {logical}")
    relative = logical[len(config.frontend_path_prefix):]
    if not relative.startswith("src/"):
        raise ValueError(f"frontend path missing src/: {logical}")
    return config.vben_root / config.frontend_app_root / relative[len("src/"):]


def map_backend_path(logical: str, config: ProjectConfig) -> Path:
    """把清单里的后端逻辑路径映射到 boot 仓库。"""
    if not logical.startswith(config.backend_path_prefix):
        raise ValueError(f"backend path does not match prefix: {logical}")
    return config.boot_root / logical


def module_sql_path(config: ProjectConfig, module: str) -> Path:
    """返回模块基线 SQL 路径。"""
    return config.sql_dir / f"{config.sql_module_prefix}{module}.sql"


def new_module_sql(module: str, prelude: list[str]) -> str:
    """返回符合新结构的最小模块 SQL 骨架。"""
    if not prelude:
        raise ConfigError("missing config field: sqlPrelude")
    order = " → ".join([*prelude, "本文件"])
    return (
        "-- ----------------------------\n"
        f"-- fan-module-{module}.sql\n"
        f"-- {module} 模块\n"
        "-- 依赖：system 模块的 system_menu、system_dict_type、system_dict_data。\n"
        f"-- 执行顺序：{order}\n"
        "-- 本文件只负责建表与预置数据；删表语句见 fan-drop.sql\n"
        "-- ----------------------------\n"
        "SET NAMES utf8mb4;\n"
        "-- 关闭外键检查\n"
        "SET FOREIGN_KEY_CHECKS = 0;\n\n"
        "-- 恢复外键检查\n"
        "SET FOREIGN_KEY_CHECKS = 1;\n"
    )


def all_module_sql(config: ProjectConfig) -> str:
    """聚合所有模块 SQL，用于全局菜单取号。"""
    files = sorted(config.sql_dir.glob(f"{config.sql_module_prefix}*.sql"))
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def next_menu_id(sql: str, table: str = "system_menu", start_id: int | None = None) -> int:
    """返回菜单表下一个可用编号。"""
    ids = [int(value) for value in re.findall(
        r"INSERT INTO `" + re.escape(table) + r"` .*?VALUES \((\d+),", sql, re.S)]
    if not ids:
        if re.search(r"INSERT INTO `" + re.escape(table) + r"`", sql, re.S):
            raise ValueError(f"cannot parse menu rows in {table}")
        return start_id or 1
    return max(max(ids) + 1, start_id or 1)


def append_menu_sql(sql: str, statements: list[str], table: str = "system_menu") -> str:
    """把菜单语句追加到菜单表 seed 末尾。"""
    pattern = re.compile(r"^INSERT INTO `" + re.escape(table) + r"` .*?;\s*$", re.M | re.S)
    matches = list(pattern.finditer(sql))
    if matches:
        position = matches[-1].end()
    else:
        position = sql.find("SET FOREIGN_KEY_CHECKS = 1")
        if position < 0:
            position = len(sql)
    return sql[:position] + "\n" + "\n".join(statements) + sql[position:]


def ensure_auto_increment(ddl: str, value: int = 10001) -> str:
    """把表选项 AUTO_INCREMENT 规范为指定值；没有自增列时原样返回。"""
    if "AUTO_INCREMENT" not in ddl.upper():
        return ddl
    if re.search(r"AUTO_INCREMENT\s*=\s*\d+", ddl, re.I):
        return re.sub(r"AUTO_INCREMENT\s*=\s*\d+", f"AUTO_INCREMENT = {value}", ddl, count=1, flags=re.I)
    if re.search(r"ENGINE\s*=\s*InnoDB", ddl, re.I):
        return re.sub(r"ENGINE\s*=\s*InnoDB", f"ENGINE = InnoDB AUTO_INCREMENT = {value}", ddl, count=1, flags=re.I)
    # 没有 ENGINE 表选项时，在语句结尾补 AUTO_INCREMENT
    head, separator, tail = ddl.rpartition(";")
    if separator:
        return f"{head.rstrip()} AUTO_INCREMENT = {value};{tail}"
    return f"{ddl.rstrip()} AUTO_INCREMENT = {value}"


def _menu_row_id(row: str) -> int:
    match = re.search(r"VALUES \((\d+),", row)
    if not match:
        raise ValueError(f"cannot parse menu id: {row[:80]}")
    return int(match.group(1))


def _insert_one_menu_row(sql: str, row: str, table: str) -> str:
    row_re = re.compile(r"^INSERT INTO `" + re.escape(table) + r"` .*?VALUES \((\d+),", re.S | re.M)
    existing = [(int(match.group(1)), match.start()) for match in row_re.finditer(sql)]
    new_id = _menu_row_id(row)
    if existing:
        position = next((start for value, start in existing if value > new_id), None)
        if position is None:
            semicolon = sql.find(";", existing[-1][1])
            line_end = sql.find("\n", semicolon) if semicolon >= 0 else -1
            position = line_end + 1 if line_end >= 0 else len(sql)
        return sql[:position] + row + "\n" + sql[position:]
    anchor = sql.find("-- 恢复外键检查")
    if anchor < 0:
        anchor = sql.find("SET FOREIGN_KEY_CHECKS = 1")
    if anchor < 0:
        anchor = len(sql)
    block = ("-- ----------------------------\n"
             f"-- Records of {table}\n"
             "-- ----------------------------\n"
             "BEGIN;\n" + row + "\nCOMMIT;\n\n")
    return sql[:anchor] + block + sql[anchor:]


def insert_menu_rows(sql: str, statements: list[str], table: str = "system_menu") -> str:
    """按 id 顺序逐条插入菜单行；没有记录段时创建记录段。"""
    for row in sorted(statements, key=_menu_row_id):
        sql = _insert_one_menu_row(sql, row, table)
    return sql


def _normalize_ddl(ddl: str) -> str:
    lines = ddl.strip().splitlines()
    while lines and lines[0].lstrip().startswith("--"):
        lines.pop(0)
    text = "\n".join(lines).strip()
    text = re.sub(r"(?is)DROP TABLE IF EXISTS\s+`?\w+`?\s*;\s*", "", text).strip()
    text = ensure_auto_increment(text)
    if not text.endswith(";"):
        text += ";"
    return text


def _section_start(sql: str, position: int) -> int:
    """返回 position 所在 section 上方分隔线的起点；没有分隔线时返回 position。"""
    line_start = sql.rfind("\n", 0, position) + 1
    if line_start <= 0:
        return position
    prev_end = line_start - 1
    prev_start = sql.rfind("\n", 0, prev_end) + 1
    if sql[prev_start:prev_end].strip() == "-- ----------------------------":
        return prev_start
    return position


def insert_table_ddl(sql: str, table: str, ddl: str) -> str:
    """按表名顺序插入 DDL 段。"""
    markers = list(TABLE_MARKER.finditer(sql))
    if any(marker.group(1) == table for marker in markers):
        raise ValueError(f"table already exists in sql: {table}")
    position = next((marker.start() for marker in markers if marker.group(1) > table), None)
    if position is not None:
        position = _section_start(sql, position)
    if position is None:
        for anchor in ("-- Records of ", "-- 恢复外键检查", "SET FOREIGN_KEY_CHECKS = 1"):
            found = sql.find(anchor)
            if found >= 0:
                position = _section_start(sql, found) if anchor.startswith("-- Records") else found
                break
    if position is None:
        position = len(sql)
    block = _normalize_ddl(ddl)
    block = ("-- ----------------------------\n"
             f"-- Table structure for {table}\n"
             "-- ----------------------------\n"
             f"{block}\n")
    prefix = sql[:position]
    if prefix and not prefix.endswith("\n\n"):
        prefix = prefix.rstrip("\n") + "\n\n"
    return prefix + block + "\n" + sql[position:]


def append_drop_tables(sql_dir: Path, module: str, tables: list[str]) -> None:
    """把新表以注释态 DROP 追加到 fan-drop.sql 的模块分组。"""
    path = sql_dir / "fan-drop.sql"
    text = path.read_text(encoding="utf-8") if path.exists() else (
        "-- ----------------------------\n"
        "-- fan-drop.sql\n"
        "-- 注意：DROP 默认全部注释。\n"
        "-- ----------------------------\n"
        "SET NAMES utf8mb4;\n"
        "-- 关闭外键检查\n"
        "SET FOREIGN_KEY_CHECKS = 0;\n\n"
        "-- 恢复外键检查\n"
        "SET FOREIGN_KEY_CHECKS = 1;\n"
    )
    if not tables:
        return
    marker = f"-- {module} 模块"
    rows = "\n".join(f"-- DROP TABLE IF EXISTS `{name}`;"
                     for name in sorted(tables, reverse=True))
    if marker in text:
        start = text.index(marker)
        end = text.find("\n\n", start)
        if end < 0:
            end = len(text)
        marker_end = text.find("\n", start) + 1
        separator_end = text.find("\n", marker_end)
        separator_end = separator_end + 1 if separator_end >= 0 else marker_end
        existing = re.findall(r"`([^`]+)`", text[separator_end:end])
        names = sorted(set(existing) | set(tables), reverse=True)
        body = "\n".join(f"-- DROP TABLE IF EXISTS `{name}`;" for name in names)
        text = text[:separator_end] + body + text[end:]
    else:
        block = ("-- ----------------------------\n"
                 f"{marker}\n"
                 "-- ----------------------------\n"
                 f"{rows}\n\n")
        anchor = text.find("-- 恢复外键检查")
        if anchor < 0:
            anchor = len(text)
        text = text[:anchor] + block + text[anchor:]
    path.write_text(text, encoding="utf-8")


def merge_error_code_entries(source: str, entries: list[dict], start_code: int) -> str:
    """把错误码条目合并到模块常量文件，跳过同名常量。"""
    existing = set(re.findall(r"ErrorCode\s+(\w+)\s*=", source))
    used = set()
    for value in re.findall(r"new ErrorCode\((\d[\d_]*),", source):
        used.add(int(value.replace("_", "")))
    next_code = start_code
    while next_code in used:
        next_code += 1
    lines = []
    for entry in entries:
        name, message = entry["name"], entry["message"]
        if name in existing:
            continue
        lines.append(f'    ErrorCode {name} = new ErrorCode({format(next_code, "_")}, "{message}");')
        existing.add(name)
        used.add(next_code)
        next_code += 1
    if not lines:
        return source
    position = source.rfind("}")
    return source[:position] + "\n" + "\n".join(lines) + "\n" + source[position:]


def ensure_error_code_import(source: str, base_package: str) -> str:
    """常量文件出现 ErrorCode 时补上导入，已有则不重复。"""
    if "new ErrorCode(" not in source and not re.search(r"\bErrorCode\s+\w+\s*=", source):
        return source
    line = f"import {base_package}.framework.common.exception.ErrorCode;\n"
    if line in source:
        return source
    match = re.search(r"package [^;]+;\n", source)
    if not match:
        return line + source
    return source[:match.end()] + "\n" + line + source[match.end():]


def merge_error_codes(source: str, manual: str, start_code: int) -> str:
    """兼容手动 Java 文件：抽成条目后合并。"""
    entries = [{"name": match.group(1), "message": match.group(2)}
               for match in ERROR_CODE.finditer(manual)]
    return merge_error_code_entries(source, entries, start_code)



def load_bundle(zip_path: Path, workdir: Path) -> dict:
    """解压 ZIP 并读取清单。"""
    workdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if ".." in Path(name).parts:
                raise ValueError(f"unsafe zip entry: {name}")
        archive.extractall(workdir)
    return json.loads((workdir / "manifest.json").read_text(encoding="utf-8"))


class FileConflict(RuntimeError):
    pass


BASELINE_DIR = Path(".tmp") / "f-base-codegen-base"

_COLUMN_FIELD = re.compile(r"field:\s*'(\w+)',([\s\S]*?)(?=\n\s*\},)")
_COLUMN_PROP = re.compile(r"(align|headerAlign):\s*'([^']*)'")
_METHOD_BLOCK = re.compile(
    r"((?:export\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})"
)
_SELECT_PAGE = re.compile(
    r"(selectPage\b[\s\S]*?)(?=\n\s*(?:export\s+)?function\s+\w+|\Z)"
)
_JAVA_FIELD = re.compile(
    r"((?:/\*\*[\s\S]*?\*/\s*)?(?:@[^\n]+\n\s*)*(?:private|protected|public)\s+[^\n;]+;)"
)
_LINK_TAG = re.compile(r"\{@link\s+([^}]+)\}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(path: Path, copied: list[tuple[Path, Path]]) -> None:
    state = {}
    for source, target in copied:
        state[str(target)] = {"source": _sha256(source), "target": _sha256(target)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def baseline_path(workspace: Path, logical: str) -> Path:
    """返回逻辑路径对应的基线文件。"""
    return workspace / BASELINE_DIR / logical


def _column_props(text: str) -> dict[str, dict[str, str]]:
    """按 field 收集 align / headerAlign。"""
    props: dict[str, dict[str, str]] = {}
    for match in _COLUMN_FIELD.finditer(text):
        field = match.group(1)
        body = match.group(2)
        field_props = {key: value for key, value in _COLUMN_PROP.findall(body)}
        if field_props:
            props[field] = field_props
    return props


def _apply_column_props(text: str, props: dict[str, dict[str, str]]) -> str:
    """把指定列的 align / headerAlign 写回文本。"""

    def replace(match: re.Match) -> str:
        field = match.group(1)
        body = match.group(2)
        for key, value in props.get(field, {}).items():
            body = _set_ts_prop(body, key, value)
        return f"field: '{field}',{body}"

    return _COLUMN_FIELD.sub(replace, text)


def _methods(text: str) -> dict[str, str]:
    """方法名 → 完整方法文本。"""
    return {match.group(2): match.group(1) for match in _METHOD_BLOCK.finditer(text)}


def _prefer_filled_links(current: str, new: str) -> str:
    """当前已有无 TODO 的 {@link} 时，不让新结果的 TODO 链接盖掉。"""
    current_links = [match.group(0) for match in _LINK_TAG.finditer(current)
                     if "TODO" not in match.group(1)]
    if not current_links:
        return new

    result = new
    index = 0

    def replace(match: re.Match) -> str:
        nonlocal index
        if "TODO" in match.group(1) and index < len(current_links):
            filled = current_links[index]
            index += 1
            return filled
        return match.group(0)

    return _LINK_TAG.sub(replace, result)


def _merge_without_baseline(current: str, new: str) -> str:
    """无基线：以新结果为结构，保留人对齐、已填链接和多余方法。"""
    result = new
    props = _column_props(current)
    if props:
        result = _apply_column_props(result, props)
    result = _prefer_filled_links(current, result)
    new_methods = _methods(new)
    extras = [body for name, body in _methods(current).items() if name not in new_methods]
    if extras:
        result = result.rstrip() + "\n" + "\n".join(extras) + "\n"
    return result


def _extract_units(text: str) -> dict[str, str]:
    """拆成字段 / 列属性 / selectPage 块 / 方法；识别不到时整文件一块。"""
    units: dict[str, str] = {}
    for match in _COLUMN_FIELD.finditer(text):
        field = match.group(1)
        body = match.group(2)
        units[f"field:{field}"] = match.group(0)
        for key, value in _COLUMN_PROP.findall(body):
            units[f"prop:{field}:{key}"] = value
    for match in _SELECT_PAGE.finditer(text):
        units["selectPage"] = match.group(1)
    for name, body in _methods(text).items():
        units[f"method:{name}"] = body
    for index, match in enumerate(_JAVA_FIELD.finditer(text)):
        units[f"java-field:{index}"] = match.group(1)
    # 裸 align 片段（单测用）
    if not units:
        for key, value in _COLUMN_PROP.findall(text):
            units[f"prop::{key}"] = value
    if not units:
        units["__file__"] = text
    return units


def _merge_three_way(baseline: str, current: str, new: str) -> str:
    """有基线：按单位三方对比；同一单位两边都改则整文件冲突。"""
    base_units = _extract_units(baseline)
    current_units = _extract_units(current)
    new_units = _extract_units(new)
    keys = set(base_units) | set(current_units) | set(new_units)
    for key in keys:
        base_value = base_units.get(key)
        current_value = current_units.get(key)
        new_value = new_units.get(key)
        current_changed = current_value != base_value
        new_changed = new_value != base_value
        if current_changed and new_changed and current_value != new_value:
            raise FileConflict(f"both sides changed: {key}")
    # 以新结果为底，按单位套回「仅当前改过」的块
    result = new
    for key, current_value in current_units.items():
        base_value = base_units.get(key)
        new_value = new_units.get(key)
        if current_value == base_value:
            continue
        if new_value != base_value:
            continue
        if key.startswith("prop:"):
            _, field, prop = key.split(":", 2)
            if field:
                result = _apply_column_props(result, {field: {prop: current_value}})
            else:
                result = re.sub(
                    rf"{prop}:\s*'[^']*'", f"{prop}: '{current_value}'", result, count=1)
        elif key.startswith("method:"):
            name = key.split(":", 1)[1]
            if name not in _methods(result):
                result = result.rstrip() + "\n" + current_value + "\n"
        elif key == "selectPage" and "selectPage" in result:
            result = _SELECT_PAGE.sub(current_value, result, count=1)
        elif key.startswith("field:") or key.startswith("java-field:"):
            if key in new_units and new_units[key] == base_value:
                result = result.replace(new_units[key], current_value, 1)
        elif key == "__file__":
            return current
    return result


def merge_generated(baseline: str | None, current: str, new: str) -> str:
    """三方合并生成物。baseline 为 None 表示无基线。"""
    if baseline is None:
        return _merge_without_baseline(current, new)
    return _merge_three_way(baseline, current, new)


def copy_sources(manifest: dict, workdir: Path, config: ProjectConfig,
                 dry_run: bool, force: bool = False, state: dict | None = None,
                 workspace: Path | None = None) -> list[tuple[Path, Path]]:
    """复制源码；有目标时按基线三方合并，冲突则跳过该文件。"""
    copied = []
    state = state or {}
    workspace = workspace or Path.cwd()
    for item in manifest["files"]:
        logical = item["path"]
        kind = item["kind"]
        if kind == "backend":
            target = map_backend_path(logical, config)
        elif kind == "frontend":
            target = map_frontend_path(logical, manifest.get("frontType", config.front_type), config)
        else:
            continue
        source_path = workdir / logical
        new_content = source_path.read_text(encoding="utf-8")
        content = new_content
        if target.exists() and not force:
            current = target.read_text(encoding="utf-8")
            base_file = baseline_path(workspace, logical)
            baseline = base_file.read_text(encoding="utf-8") if base_file.exists() else None
            if current == new_content:
                content = new_content
            else:
                try:
                    content = merge_generated(baseline, current, new_content)
                except FileConflict as error:
                    print(f"conflict skip {target}: {error}")
                    continue
        if dry_run:
            print(f"{logical} -> {target}")
            copied.append((source_path, target))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        base_file = baseline_path(workspace, logical)
        base_file.parent.mkdir(parents=True, exist_ok=True)
        base_file.write_text(new_content, encoding="utf-8")
        copied.append((source_path, target))
    return copied


MENU_ICONS = {
    "ep:avatar", "ep:chat-dot-round", "ep:collection", "ep:connection",
    "ep:document", "ep:document-copy", "ep:house", "ep:link", "ep:list",
    "ep:menu", "ep:message", "ep:message-box", "ep:position", "ep:promotion",
    "ep:set-up", "ep:takeaway-box", "ep:tools", "ep:user",
}
BUTTON_LABELS = {
    "query": "查询", "create": "创建", "update": "更新",
    "delete": "删除", "export": "导出", "import": "导入",
}
ALIGN_BY_CATEGORY = {
    "编号": "center", "状态": "center", "时间": "center",
    "短名称": "left", "中等文本": "left", "长文本": "left",
}
_MENU_NAME = re.compile(r"^[\u4e00-\u9fff]{2,6}$")


def rewrite_menu_plan(plan: dict, decision: dict) -> dict:
    """按菜单结论改写计划。已有父菜单不改名称、路径和图标。"""
    menu_name = decision["menuName"]
    menu_icon = decision["menuIcon"]
    if not _MENU_NAME.match(menu_name) or "管理" in menu_name:
        raise ValueError(f"页面菜单名必须是 2–6 个汉字且不带「管理」: {menu_name}")
    if menu_icon not in MENU_ICONS:
        raise ValueError(f"图标不在清单内: {menu_icon}")
    if decision.get("parentExists"):
        plan["parent"]["name"] = decision["existingParentName"]
        plan["parent"]["path"] = decision["existingParentPath"]
        plan["parent"]["icon"] = decision["existingParentIcon"]
    else:
        parent_name = decision["parentName"]
        parent_icon = decision["parentIcon"]
        if not _MENU_NAME.match(parent_name):
            raise ValueError(f"父菜单名必须是 2–6 个汉字: {parent_name}")
        if parent_icon not in MENU_ICONS:
            raise ValueError(f"图标不在清单内: {parent_icon}")
        plan["parent"]["name"] = parent_name
        plan["parent"]["icon"] = parent_icon
    plan["menu"]["name"] = menu_name
    plan["menu"]["icon"] = menu_icon
    for button in plan.get("buttons") or []:
        operation = str(button.get("permission") or "").rsplit(":", 1)[-1]
        label = BUTTON_LABELS.get(operation)
        if label:
            button["name"] = menu_name + label
    return plan


def _set_ts_prop(body: str, key: str, value: str) -> str:
    """在列对象片段里写入或替换字符串属性。"""
    pattern = rf"{key}:\s*'[^']*'"
    if re.search(pattern, body):
        return re.sub(pattern, f"{key}: '{value}'", body, count=1)
    return body.rstrip() + f"\n      {key}: '{value}',\n    "


def apply_column_align(text: str, categories: dict) -> str:
    """给 useGridColumns 的数据列写入对齐。表头一律居中，单元格按类别。操作列不写。"""

    def replace(match: re.Match) -> str:
        field = match.group(1)
        body = match.group(2)
        category = categories.get(field)
        if category is None:
            return match.group(0)
        align = ALIGN_BY_CATEGORY.get(category)
        if align is None:
            raise ValueError(f"未知列宽类别: {field}={category}")
        body = _set_ts_prop(body, "headerAlign", "center")
        body = _set_ts_prop(body, "align", align)
        return f"field: '{field}',{body}"

    return re.sub(r"field: '(\w+)',([\s\S]*?)(?=\n    \},)", replace, text)


def find_menu_id(sql: str, path: str, name: str, table: str = "system_menu") -> int | None:
    """查找菜单编号。绝对 path（以 / 开头）只比 path；相对 path 必须 path 与 name 同时相同。"""
    pattern = re.compile(
        r"INSERT INTO `" + re.escape(table)
        + r"` .*?VALUES \((\d+), '([^']*)', '([^']*)', (\d+), (\d+), (\d+), '([^']*)'", re.S
    )
    for match in pattern.finditer(sql):
        row_name, row_path = match.group(2), match.group(7)
        if path.startswith("/") and row_path == path:
            return int(match.group(1))
        if not path.startswith("/") and row_path == path and row_name == name:
            return int(match.group(1))
    return None


def _quote(value: str) -> str:
    return value.replace("'", "''")


def ensure_parent_menu(sql: str, parent: dict, config: ProjectConfig | None = None,
                       module: str | None = None,
                       search_sql: str | None = None,
                       db_max: int | None = None) -> tuple[str, int, str | None]:
    """确保父菜单存在，不存在时新建根目录菜单。"""
    table = config.menu_table if config else "system_menu"
    search = search_sql if search_sql is not None else sql
    parent_id = find_menu_id(search, parent["path"], parent["name"], table)
    if parent_id is not None:
        return sql, parent_id, None
    if config and config.sql_rules_path and module:
        ids = [int(match.group(1)) for match in re.finditer(
            r"INSERT INTO `" + re.escape(table) + r"` .*?VALUES \((\d+),", search, re.S)]
        rules = load_rules(config.sql_rules_path)
        base, upper = segment_bounds(rules, module)
        start_id = next_id_in_segment(ids, base, upper)
        start_id = next_menu_start(start_id, db_max, base, upper)
        if start_id >= upper:
            raise ValueError(f"menu segment is exhausted: [{base}, {upper})")
    else:
        start_id = next_menu_id(search, table, config.menu_start_id if config else None)
        if db_max is not None:
            start_id = max(start_id, db_max + 1)
    row = (
        f"INSERT INTO `{table}` (`id`, `name`, `permission`, `type`, `sort`, `parent_id`, "
        "`path`, `icon`, `component`, `component_name`, `status`, `visible`, `keep_alive`, "
        "`always_show`, `creator`, `create_time`, `updater`, `update_time`, `deleted`) VALUES "
        f"({start_id}, '{_quote(parent['name'])}', '', 1, 10, 0, "
        f"'{_quote(parent['path'])}', '{_quote(parent.get('icon') or 'ep:menu')}', NULL, NULL, 0, "
        "b'1', b'1', b'1', 'admin', CURRENT_TIMESTAMP, '1', CURRENT_TIMESTAMP, b'0');"
    )
    return insert_menu_rows(sql, [row], table), start_id, row


def render_menu_sql(plan: dict, parent_id: int, start_id: int,
                    table: str = "system_menu") -> list[str]:
    """按项目格式渲染菜单和按钮 SQL。"""
    menu = plan["menu"]
    lines = [
        f"INSERT INTO `{table}` (`id`, `name`, `permission`, `type`, `sort`, `parent_id`, "
        "`path`, `icon`, `component`, `component_name`, `status`, `visible`, `keep_alive`, "
        "`always_show`, `creator`, `create_time`, `updater`, `update_time`, `deleted`) VALUES "
        f"({start_id}, '{_quote(menu['name'])}', '', {menu['type']}, {menu['sort']}, {parent_id}, "
        f"'{_quote(menu['path'])}', '{_quote(menu['icon'] or '')}', '{_quote(menu['component'])}', "
        f"'{_quote(menu['componentName'])}', 0, b'1', b'1', b'1', 'admin', CURRENT_TIMESTAMP, "
        "'1', CURRENT_TIMESTAMP, b'0');"
    ]
    for index, button in enumerate(plan["buttons"], start=1):
        lines.append(
            f"INSERT INTO `{table}` (`id`, `name`, `permission`, `type`, `sort`, `parent_id`, "
            "`path`, `icon`, `component`, `component_name`, `status`, `visible`, `keep_alive`, "
            "`always_show`, `creator`, `create_time`, `updater`, `update_time`, `deleted`) VALUES "
            f"({start_id + index}, '{_quote(button['name'])}', '{_quote(button['permission'])}', 3, "
            f"{button['sort']}, {start_id}, '', '', '', NULL, 0, b'1', b'1', b'1', 'admin', "
            "CURRENT_TIMESTAMP, '1', CURRENT_TIMESTAMP, b'0');"
        )
    return lines


def upgrade_ddl(ddl: str) -> str:
    """增量脚本删除 DROP，规范 AUTO_INCREMENT，并让 CREATE TABLE 幂等。"""
    without_drop = re.sub(r"(?is)DROP TABLE IF EXISTS\s+`?\w+`?\s*;\s*", "", ddl)
    idempotent = re.sub(r"(?is)CREATE TABLE(?! IF NOT EXISTS)", "CREATE TABLE IF NOT EXISTS",
                        without_drop)
    return ensure_auto_increment(idempotent)


def parse_dict_values(sql: str, dict_type: str) -> list[tuple[str, str]]:
    """从模块 SQL 中读取一个字典类型的值/标签。"""
    pattern = re.compile(
        r"INSERT INTO `system_dict_data` .*?VALUES \(\d+,\s*\d+,\s*'([^']*)',\s*'([^']*)',\s*'"
        + re.escape(dict_type) + r"'")
    return [(value, label) for label, value in pattern.findall(sql)]


def _pascal(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in value.split("_") if part)


_ENUM_CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]*$")


def create_enum_file(boot: Path, base_package: str, module: str, dict_type: str,
                     values: list[tuple[str, str]], module_dir: str | None = None,
                     *, constants: list[str]) -> Path:
    """按字典值与结论中的常量名创建枚举类。"""
    if len(constants) != len(values):
        raise ValueError("constants 必须与 values 等长")
    if len(set(constants)) != len(constants):
        raise ValueError("constants 不可重复")
    for name in constants:
        if not _ENUM_CONSTANT.fullmatch(name):
            raise ValueError(f"非法枚举常量名: {name}")
    enum_name = _pascal(dict_type) + "Enum"
    domain = dict_type.split("_")[0]
    java_type = "Integer" if all(value.isdigit() for value, _ in values) else "String"
    lines = [
        f"package {base_package}.module.{module}.enums.{domain};",
        "",
    ]
    if java_type == "Integer":
        lines.extend([
            f"import {base_package}.framework.common.core.ArrayValuable;",
            "import lombok.AllArgsConstructor;",
            "import lombok.Getter;",
            "",
            "import java.util.Arrays;",
            "",
        ])
    else:
        lines.extend([
            "import lombok.AllArgsConstructor;",
            "import lombok.Getter;",
            "",
        ])
    lines.extend([
        "/**",
        f" * {dict_type} 枚举。",
        " */",
        "@Getter",
        "@AllArgsConstructor",
    ])
    if java_type == "Integer":
        lines.append(f"public enum {enum_name} implements ArrayValuable<Integer> {{")
    else:
        lines.append(f"public enum {enum_name} {{")
    lines.append("")
    body = []
    for (value, label), name in zip(values, constants):
        literal = value if java_type == "Integer" else f'"{value}"'
        body.append(f'    {name}({literal}, "{label}")')
    lines.append(",\n".join(body) + ";")
    if java_type == "Integer":
        lines.extend([
            "",
            f"    public static final Integer[] ARRAYS = Arrays.stream(values())",
            f"            .map({enum_name}::getValue).toArray(Integer[]::new);",
            "",
            "    private final Integer value;",
            "    private final String name;",
            "",
            "    @Override",
            "    public Integer[] array() {",
            "        return ARRAYS;",
            "    }",
            "}",
            "",
        ])
    else:
        lines.extend([
            "",
            f"    private final {java_type} value;",
            "    private final String name;",
            "}",
            "",
        ])
    path = (boot / (module_dir or module) / "src/main/java"
            / Path(base_package.replace(".", "/")) / "module" / module / "enums" / domain
            / f"{enum_name}.java")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def collect_insert_ids(sql: str, table: str) -> list[int]:
    """从 INSERT 语句收集某表的编号。"""
    return [int(match.group(1)) for match in re.finditer(
        rf"INSERT INTO `{re.escape(table)}` .*?VALUES \((\d+),", sql, re.S)]


def next_dict_ids(sql: str, base: int, upper: int) -> tuple[int, int]:
    """分别按 system_dict_type / system_dict_data 段内最大编号加 1。"""
    type_id = next_id_in_segment(collect_insert_ids(sql, "system_dict_type"), base, upper)
    data_id = next_id_in_segment(collect_insert_ids(sql, "system_dict_data"), base, upper)
    return type_id, data_id


def render_dict_sql(creates: list[dict], sql: str, base: int, upper: int) -> list[str]:
    """按字典结论写出类型与数据 INSERT；两表分开取号。"""
    type_id, data_id = next_dict_ids(sql, base, upper)
    lines: list[str] = []
    for item in creates:
        dict_type = item["dictType"]
        name = item.get("name") or dict_type
        lines.append(
            f"INSERT INTO `system_dict_type` (`id`, `name`, `type`, `status`, `remark`, "
            f"`creator`, `create_time`, `updater`, `update_time`, `deleted`, `deleted_time`) "
            f"VALUES ({type_id}, '{_quote(name)}', '{_quote(dict_type)}', 0, '', '1', "
            f"CURRENT_TIMESTAMP, '1', CURRENT_TIMESTAMP, b'0', NULL);")
        type_id += 1
        if type_id >= upper:
            raise ValueError(f"字典类型号段不足: 段上界 {upper}")
        for index, entry in enumerate(item["values"], start=1):
            label = entry["label"]
            value = entry["value"]
            lines.append(
                f"INSERT INTO `system_dict_data` (`id`, `sort`, `label`, `value`, `dict_type`, "
                f"`status`, `color_type`, `css_class`, `remark`, `creator`, `create_time`, "
                f"`updater`, `update_time`, `deleted`) VALUES ({data_id}, {index}, "
                f"'{_quote(label)}', '{_quote(value)}', '{_quote(dict_type)}', 0, 'default', "
                f"'', '', '1', CURRENT_TIMESTAMP, '1', CURRENT_TIMESTAMP, b'0');")
            data_id += 1
            if data_id >= upper:
                raise ValueError(f"字典数据号段不足: 段上界 {upper}")
    return lines


def find_dict_type(sql: str, dict_type: str) -> bool:
    """判断 system_dict_type 是否已有该 type。"""
    pattern = re.compile(
        r"INSERT INTO `system_dict_type` .*?VALUES \(\d+,\s*'[^']*',\s*'"
        + re.escape(dict_type) + r"'",
        re.S)
    return pattern.search(sql) is not None


def insert_dict_rows(sql: str, statements: list[str]) -> str:
    """把字典 INSERT 按表分别插入到对应记录段；不写 DROP。"""
    type_rows = [row for row in statements if "`system_dict_type`" in row]
    data_rows = [row for row in statements if "`system_dict_data`" in row]
    if type_rows:
        sql = insert_menu_rows(sql, type_rows, "system_dict_type")
    if data_rows:
        sql = insert_menu_rows(sql, data_rows, "system_dict_data")
    return sql


MODULE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,29}$")


def validate_manifest_module(manifest: dict) -> None:
    """只校验模块名格式，demo 等合法模块不再特殊拦截。"""
    module = manifest.get("moduleName")
    if not module or not MODULE_NAME_PATTERN.fullmatch(module):
        raise ConfigError(f"非法 moduleName: {module}")


def _insert_before(text: str, marker: str, block: str) -> str:
    position = text.find(marker)
    if position < 0:
        raise ConfigError(f"找不到插入位置: {marker}")
    return text[:position] + block + text[position:]


def _require_scaffold(scaffold: dict, key: str) -> None:
    if not scaffold.get(key):
        raise ConfigError(f"missing config field: {key}")


def _dependency_xml(group_id: str, artifact_id: str, version: str | None = None) -> str:
    lines = [
        "        <dependency>",
        f"            <groupId>{group_id}</groupId>",
        f"            <artifactId>{artifact_id}</artifactId>",
    ]
    if version:
        lines.append(f"            <version>{version}</version>")
    lines.append("        </dependency>")
    return "\n".join(lines) + "\n    "


def _insert_before_managed_dependencies(text: str, block: str) -> str:
    end = text.find("</dependencyManagement>")
    if end < 0:
        raise ConfigError("找不到插入位置: </dependencyManagement>")
    position = text.rfind("</dependencies>", 0, end)
    if position < 0:
        raise ConfigError("找不到插入位置: </dependencies>")
    return text[:position] + block + text[position:]


def _module_pom(group_id: str, parent_artifact_id: str, artifact_id: str,
                starters: list[str]) -> str:
    dependencies = "\n".join(
        "        <dependency>\n"
        f"            <groupId>{group_id}</groupId>\n"
        f"            <artifactId>{starter}</artifactId>\n"
        "        </dependency>"
        for starter in starters
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project xmlns="http://maven.apache.org/POM/4.0.0"\n'
        '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 '
        'http://maven.apache.org/xsd/maven-4.0.0.xsd">\n'
        "    <parent>\n"
        f"        <groupId>{group_id}</groupId>\n"
        f"        <artifactId>{parent_artifact_id}</artifactId>\n"
        "        <version>${revision}</version>\n"
        "    </parent>\n"
        "    <modelVersion>4.0.0</modelVersion>\n"
        f"    <artifactId>{artifact_id}</artifactId>\n"
        "    <packaging>jar</packaging>\n"
        "\n"
        "    <dependencies>\n"
        f"{dependencies}\n"
        "    </dependencies>\n"
        "</project>\n"
    )


def _web_configuration(base_package: str, module: str, open_api_method: str) -> str:
    class_fqcn, method_name = open_api_method.rsplit(".", 1)
    simple_name = class_fqcn.rsplit(".", 1)[-1]
    class_name = module[:1].upper() + module[1:] + "WebConfiguration"
    package = f"{base_package}.module.{module}.framework.web.config"
    return (
        f"package {package};\n"
        "\n"
        f"import {class_fqcn};\n"
        "import org.springdoc.core.models.GroupedOpenApi;\n"
        "import org.springframework.context.annotation.Bean;\n"
        "import org.springframework.context.annotation.Configuration;\n"
        "\n"
        "/**\n"
        f" * {module} 模块的 web 组件的 Configuration\n"
        " */\n"
        "@Configuration(proxyBeanMethods = false)\n"
        f"public class {class_name} {{\n"
        "\n"
        "    /**\n"
        f"     * {module} 模块的 API 分组\n"
        "     */\n"
        "    @Bean\n"
        f"    public GroupedOpenApi {module}GroupedOpenApi() {{\n"
        f'        return {simple_name}.{method_name}("{module}");\n'
        "    }\n"
        "\n"
        "}\n"
    )


def ensure_module_scaffold(config: ProjectConfig, module: str, dry_run: bool,
                           *, tenant: bool = False, export: bool = False) -> bool:
    """模块 pom.xml 不存在时，按配置创建最小 Maven 骨架。"""
    module_dir = config.boot_root / f"{config.backend_path_prefix}{module}"
    if (module_dir / "pom.xml").exists():
        return False
    scaffold = config.module_scaffold or {}
    for key in ("rootPom", "serverPom", "bomPom", "groupId", "parentArtifactId",
                "openApiMethod", "starters"):
        _require_scaffold(scaffold, key)
    if tenant:
        _require_scaffold(scaffold, "tenantStarter")
    if export:
        _require_scaffold(scaffold, "excelStarter")
    if dry_run:
        print(f"scaffold {module_dir}")
        return True
    group_id = scaffold["groupId"]
    artifact = f"{config.backend_path_prefix}{module}"
    starters = list(scaffold["starters"])
    if tenant:
        starters.append(scaffold["tenantStarter"])
    if export:
        starters.append(scaffold["excelStarter"])
    module_dir.mkdir(parents=True, exist_ok=True)
    pom_path = module_dir / "pom.xml"
    if not pom_path.exists():
        pom_path.write_text(
            _module_pom(group_id, scaffold["parentArtifactId"], artifact, starters),
            encoding="utf-8")
    package_path = Path(*config.base_package.split(".")) / "module" / module / "enums"
    error_codes = module_dir / "src/main/java" / package_path / "ErrorCodeConstants.java"
    if not error_codes.exists():
        error_codes.parent.mkdir(parents=True, exist_ok=True)
        error_codes.write_text(
            f"package {config.base_package}.module.{module}.enums;\n\n"
            "public interface ErrorCodeConstants {\n}\n", encoding="utf-8")
    class_name = module[:1].upper() + module[1:] + "WebConfiguration"
    web_path = (module_dir / "src/main/java" / Path(*config.base_package.split("."))
                / "module" / module / "framework" / "web" / "config" / f"{class_name}.java")
    if not web_path.exists():
        web_path.parent.mkdir(parents=True, exist_ok=True)
        web_path.write_text(
            _web_configuration(config.base_package, module, scaffold["openApiMethod"]),
            encoding="utf-8")
    root_pom = config.boot_root / scaffold["rootPom"]
    root_text = root_pom.read_text(encoding="utf-8")
    module_line = f"<module>{artifact}</module>"
    if module_line not in root_text:
        root_pom.write_text(
            _insert_before(root_text, "</modules>", f"        {module_line}\n    "),
            encoding="utf-8")
    server_pom = config.boot_root / scaffold["serverPom"]
    server_text = server_pom.read_text(encoding="utf-8")
    artifact_tag = f"<artifactId>{artifact}</artifactId>"
    if artifact_tag not in server_text:
        server_pom.write_text(
            _insert_before(server_text, "</dependencies>", _dependency_xml(group_id, artifact)),
            encoding="utf-8")
    bom_pom = config.boot_root / scaffold["bomPom"]
    bom_text = bom_pom.read_text(encoding="utf-8")
    if artifact_tag not in bom_text:
        bom_pom.write_text(
            _insert_before_managed_dependencies(
                bom_text, _dependency_xml(group_id, artifact, "${revision}")),
            encoding="utf-8")
    print(f"created module scaffold: {module_dir}")
    return True


def apply_sql(config: ProjectConfig, manifest: dict, workdir: Path,
              ddl_files: list[Path], dry_run: bool,
              menu_start_id: int | None = None,
              db_host: str = "127.0.0.1", db_user: str = "root",
              db_name: str | None = None,
              docker_container: str | None = None,
              menu_decision: Path | None = None,
              dict_decision: Path | None = None) -> Path | None:
    """维护模块基线并生成增量 SQL；支持主表/子表多个 DDL。"""
    module = manifest["moduleName"]
    sql_path = module_sql_path(config, module)
    sql = (sql_path.read_text(encoding="utf-8") if sql_path.exists()
           else new_module_sql(module, list(config.sql_prelude)))
    ddl_blocks = []
    for ddl_file in ddl_files:
        block = ddl_file.read_text(encoding="utf-8").replace("\\n", "\n").strip()
        if block and not block.endswith(";"):
            block += ";"
        if block:
            ddl_blocks.append(block)
    new_ddl = False
    new_tables: list[str] = []
    for block in ddl_blocks:
        match = re.search(r"CREATE TABLE\s+`?(\w+)`?", block, re.I)
        if not match:
            raise ValueError(f"cannot find table name in ddl: {block[:80]}")
        try:
            sql = insert_table_ddl(sql, match.group(1), block)
            new_ddl = True
            new_tables.append(match.group(1))
        except ValueError:
            continue
    menu_file = workdir / "menu.plan.json"
    menu_plan = json.loads(menu_file.read_text(encoding="utf-8")) if menu_file.exists() else None
    if menu_plan is not None and menu_decision is not None:
        decision = json.loads(menu_decision.read_text(encoding="utf-8"))
        rewrite_menu_plan(menu_plan, decision)
        if not dry_run:
            menu_file.write_text(json.dumps(menu_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    menu_sql = []
    parent_row = None
    if menu_plan is not None:
        parent = menu_plan["parent"]
        parent.setdefault("path", config.parent_menu_path or ("/" + module))
        all_sql = all_module_sql(config) + "\n" + sql
        db_parent_id = None
        if db_name:
            db_parent_id = query_menu_id(db_host, db_user, db_name, docker_container,
                                         parent["path"], parent["name"], config.menu_table)
        parent_row = None
        if db_parent_id is not None:
            parent_id = db_parent_id
        else:
            db_max = None
            if db_name:
                if config.sql_rules_path:
                    rules = load_rules(config.sql_rules_path)
                    base, upper = segment_bounds(rules, module)
                    db_max = query_menu_max_in_segment(
                        db_host, db_user, db_name, docker_container,
                        config.menu_table, base, upper)
                else:
                    db_max = query_menu_max(
                        db_host, db_user, db_name, docker_container, config.menu_table)
            sql, parent_id, parent_row = ensure_parent_menu(
                sql, parent, config, module, all_sql, db_max)
            # 父菜单可能刚插入，重新聚合内存 SQL，避免菜单重复占用父菜单编号
            all_sql = all_module_sql(config) + "\n" + sql
        if config.sql_rules_path:
            rules = load_rules(config.sql_rules_path)
            base, upper = segment_bounds(rules, module)
            ids = [int(match.group(1)) for match in re.finditer(
                r"INSERT INTO `" + re.escape(config.menu_table) + r"` .*?VALUES \((\d+),",
                all_sql, re.S)]
            local_start = next_id_in_segment(ids, base, upper)
            floor = menu_start_id or config.menu_start_id
            if floor and floor >= upper:
                raise ValueError(f"menuStartId {floor} 超出模块号段 [{base}, {upper})")
            if floor:
                local_start = max(local_start, floor)
            db_max = query_menu_max_in_segment(db_host, db_user, db_name, docker_container,
                                               config.menu_table, base, upper) if db_name else None
            start_id = next_menu_start(local_start, db_max, base, upper)
            count = 1 + len(menu_plan.get("buttons", []))
            if start_id + count - 1 >= upper:
                raise ValueError(f"菜单号段不足: 从 {start_id} 需要 {count} 个，段上界 {upper}")
        else:
            local_start = next_menu_id(all_sql, config.menu_table,
                                       menu_start_id or config.menu_start_id)
            print("warning: sqlRulesPath 未配置，回退到全局最大编号 + 1")
            db_max = query_menu_max(db_host, db_user, db_name, docker_container,
                                    config.menu_table) if db_name else None
            start_id = max(local_start, (db_max or 0) + 1)
        menu_sql = render_menu_sql(menu_plan, parent_id, start_id, config.menu_table)
        if find_menu_id(all_sql, menu_plan["menu"]["path"], menu_plan["menu"]["name"],
                        config.menu_table) is not None:
            menu_sql = []
    dict_sql: list[str] = []
    if dict_decision is not None:
        dict_plan = json.loads(dict_decision.read_text(encoding="utf-8"))
        creates = list(dict_plan.get("creates") or [])
        if creates:
            if not config.sql_rules_path:
                raise ConfigError("dict creates 需要 sqlRulesPath")
            rules = load_rules(config.sql_rules_path)
            base, upper = segment_bounds(rules, module)
            search = all_module_sql(config) + "\n" + sql
            fresh = []
            for item in creates:
                dict_type = item["dictType"]
                if find_dict_type(search, dict_type):
                    print(f"skip dict type {dict_type}")
                else:
                    fresh.append(item)
            if fresh:
                dict_sql = render_dict_sql(fresh, sql, base, upper)
    if not (new_ddl or menu_sql or dict_sql):
        print("already applied")
        return None
    if menu_sql:
        sql = insert_menu_rows(sql, menu_sql, config.menu_table)
    if dict_sql:
        sql = insert_dict_rows(sql, dict_sql)
    if dry_run:
        print(f"update {sql_path}")
        return None
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.write_text(sql, encoding="utf-8")
    if new_tables:
        append_drop_tables(config.sql_dir, module, new_tables)
    base_name = (f"{datetime.date.today().isoformat()}-{module}-"
                 f"{manifest['businessName'].replace('/', '-')}")
    upgrade = config.sql_dir / "upgrade" / f"{base_name}.sql"
    index = 2
    while upgrade.exists():
        upgrade = config.sql_dir / "upgrade" / f"{base_name}-{index}.sql"
        index += 1
    upgrade.parent.mkdir(parents=True, exist_ok=True)
    menu_statements = ([parent_row] if parent_row else []) + menu_sql
    parts = [upgrade_ddl(block) for block in ddl_blocks] if new_ddl else []
    if menu_statements:
        parts.append("\n".join(menu_statements))
    if dict_sql:
        parts.append("\n".join(dict_sql))
    upgrade.write_text("\n\n".join(parts).strip(), encoding="utf-8")
    return upgrade

def ensure_dict_constant(config: ProjectConfig, module: str, dict_type: str) -> None:
    """在模块字典常量文件中补充常量；文件不存在时创建。"""
    module_dir = config.backend_path_prefix + module
    targets = list(config.boot_root.glob(f"{module_dir}/src/main/java/**/enums/DictTypeConstants.java"))
    constant = re.sub(r"\W+", "_", dict_type).upper()
    if targets:
        target = targets[0]
        source = target.read_text(encoding="utf-8")
        if f'"{dict_type}"' in source:
            return
        position = source.rfind("}")
        source = source[:position] + f'\n    String {constant} = "{dict_type}";\n' + source[position:]
        target.write_text(source, encoding="utf-8")
        return
    package_path = config.base_package.replace(".", "/")
    target = (config.boot_root / module_dir / "src/main/java" / package_path
              / "module" / module / "enums" / "DictTypeConstants.java")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"package {config.base_package}.module.{module}.enums;\n\n"
        f"public interface DictTypeConstants {{\n\n"
        f'    String {constant} = "{dict_type}";\n'
        f"}}\n",
        encoding="utf-8",
    )


def _dict_constant_name(dict_type: str) -> str:
    return re.sub(r"\W+", "_", dict_type).upper()


def ensure_dict_type_constants_import(source: str, base_package: str, module: str) -> str:
    """Java 文件使用 DictTypeConstants 时补上导入，已有则不重复。"""
    line = f"import {base_package}.module.{module}.enums.DictTypeConstants;\n"
    if line.strip() in source:
        return source
    match = re.search(r"package [^;]+;\n", source)
    if not match:
        return line + source
    return source[:match.end()] + "\n" + line + source[match.end():]


def _replace_dict_todos(text: str, dict_type: str, enum_ref: str, constant: str) -> str:
    """把字典 TODO 换成枚举全名与 DictTypeConstants 常量。"""
    text = text.replace(f"TODO {dict_type} 对应的类", enum_ref)
    text = text.replace(
        f'@DictFormat("{dict_type}") // TODO 代码优化：建议设置到对应的 DictTypeConstants 枚举类中',
        f"@DictFormat(DictTypeConstants.{constant})",
    )
    return text


def ensure_frontend_dict_key(vben_root: Path, module: str, dict_type: str) -> None:
    """在 packages/constants/src/dict-enum.ts 的模块分组中补同名键；已存在则跳过。"""
    path = vben_root / "packages/constants/src/dict-enum.ts"
    if not path.exists():
        raise ConfigError(f"找不到前端字典常量文件: {path}")
    text = path.read_text(encoding="utf-8")
    constant = _dict_constant_name(dict_type)
    if re.search(rf"\b{re.escape(constant)}\s*:", text):
        return
    group_name = f"{module.upper()}_DICT"
    entry = f"  {constant}: '{dict_type}',"
    group_pattern = re.compile(
        rf"(const {re.escape(group_name)} = \{{)(.*?)(\n\}} as const;)",
        re.S,
    )
    match = group_pattern.search(text)
    if match:
        body = match.group(2)
        insertion = body if body.endswith("\n") else body + "\n"
        insertion += entry + "\n"
        text = text[:match.start(2)] + insertion + text[match.end(2):]
    else:
        block = (
            f"\n/** ========== {module.upper()} ========== */\n"
            f"const {group_name} = {{\n"
            f"{entry}\n"
            f"}} as const;\n"
        )
        dict_type_match = re.search(r"\nconst DICT_TYPE = \{", text)
        if dict_type_match:
            text = text[:dict_type_match.start()] + block + text[dict_type_match.start():]
        else:
            text = text.rstrip() + "\n" + block
        spread = f"  ...{group_name},"
        if spread not in text:
            spread_anchor = re.search(r"(const DICT_TYPE = \{\n)", text)
            if spread_anchor:
                text = (text[:spread_anchor.end()] + f"{spread}\n"
                        + text[spread_anchor.end():])
            else:
                raise ConfigError("dict-enum.ts 缺少 DICT_TYPE 展开")
    path.write_text(text, encoding="utf-8")


def _validate_dict_decision(config: ProjectConfig, decision: dict) -> tuple[
        list[dict], dict[str, dict]]:
    """校验 dict-decision 全文；全部通过后才允许落盘。返回 (columns, creates_by_type)。"""
    columns = list(decision.get("columns") or [])
    creates = list(decision.get("creates") or [])
    actions_by_col: dict[str, set[str]] = {}
    for item in columns:
        col = item.get("column")
        action = item.get("action")
        if not col or not action:
            raise ConfigError("dict-decision columns 需要 column 与 action")
        if action not in ("bind", "create", "none"):
            raise ConfigError(f"未知 dict action: {action}")
        actions_by_col.setdefault(col, set()).add(action)
    for col, actions in actions_by_col.items():
        if "bind" in actions and "create" in actions:
            raise ConfigError(f"同一列不能同时 bind 与 create: {col}")

    creates_by_type: dict[str, dict] = {}
    for item in creates:
        dict_type = item.get("dictType")
        if not dict_type:
            raise ConfigError("dict-decision creates 需要 dictType")
        if dict_type in creates_by_type:
            raise ConfigError(f"creates 重复 dictType: {dict_type}")
        values = item.get("values")
        if not isinstance(values, list) or not values:
            raise ConfigError(f"creates 缺少 values: {dict_type}")
        constants: list[str] = []
        for index, entry in enumerate(values):
            if not isinstance(entry, dict):
                raise ConfigError(f"creates[{dict_type}] values[{index}] 必须是对象")
            missing = [key for key in ("value", "label", "constant") if not entry.get(key)]
            if missing:
                raise ConfigError(
                    f"creates[{dict_type}] values[{index}] 缺少字段: {', '.join(missing)}")
            name = entry["constant"]
            if not _ENUM_CONSTANT.fullmatch(name):
                raise ConfigError(f"非法枚举常量名: {name}")
            constants.append(name)
        if len(set(constants)) != len(constants):
            raise ConfigError(f"字典常量名重复: {dict_type}")
        creates_by_type[dict_type] = item

    for item in columns:
        action = item["action"]
        if action == "none":
            continue
        dict_type = item.get("dictType")
        if not dict_type:
            raise ConfigError(f"dict-decision {action} 缺少 dictType: {item.get('column')}")
        if action == "bind":
            if not enum_reference(config, dict_type):
                raise ConfigError(f"enums 对照表缺少字典类型类名: {dict_type}")
        elif action == "create":
            if dict_type not in creates_by_type:
                raise ConfigError(f"create 缺少 creates 条目: {dict_type}")
    return columns, creates_by_type


def apply_dict_decision(config: ProjectConfig, module: str, decision: dict,
                        replace_root: Path, manifest_files: list[dict]) -> None:
    """以 dict-decision.json 为唯一输入：建枚举、消 TODO、补前端键。"""
    columns, creates_by_type = _validate_dict_decision(config, decision)
    module_dir = config.backend_path_prefix + module

    def rewrite_java(dict_type: str, enum_ref: str) -> None:
        constant = _dict_constant_name(dict_type)
        for file in manifest_files:
            if file.get("kind") != "backend" or not str(file.get("path", "")).endswith(".java"):
                continue
            target = replace_root / file["path"]
            if not target.exists():
                continue
            text = target.read_text(encoding="utf-8")
            updated = _replace_dict_todos(text, dict_type, enum_ref, constant)
            if updated == text:
                continue
            if f"DictTypeConstants.{constant}" in updated:
                updated = ensure_dict_type_constants_import(
                    updated, config.base_package, module)
            target.write_text(updated, encoding="utf-8")

    for item in columns:
        action = item["action"]
        if action == "none":
            continue
        dict_type = item["dictType"]
        if action == "bind":
            reference = enum_reference(config, dict_type) or ""
            ensure_dict_constant(config, module, dict_type)
            rewrite_java(dict_type, reference)
        else:
            create_item = creates_by_type[dict_type]
            values = [(entry["value"], entry["label"]) for entry in create_item["values"]]
            constants = [entry["constant"] for entry in create_item["values"]]
            enum_path = create_enum_file(
                config.boot_root, config.base_package, module, dict_type, values,
                module_dir, constants=constants)
            enum_ref = (f"{config.base_package}.module.{module}.enums."
                        f"{dict_type.split('_')[0]}.{enum_path.stem}")
            ensure_dict_constant(config, module, dict_type)
            rewrite_java(dict_type, enum_ref)
            ensure_frontend_dict_key(config.vben_root, module, dict_type)


def maybe_apply_dict_decision(config: ProjectConfig, manifest: dict,
                              replace_root: Path,
                              dict_decision: Path | None) -> None:
    """枚举与 TODO 只走 dict-decision；缺省跳过，不按 ZIP dicts 猜测。"""
    if dict_decision is None:
        return
    decision = json.loads(dict_decision.read_text(encoding="utf-8"))
    apply_dict_decision(
        config, manifest["moduleName"], decision,
        replace_root=replace_root, manifest_files=manifest.get("files") or [])


def apply_column_align_sources(root: Path, manifest: dict, categories: dict) -> None:
    """给包内 views/*/data.ts 写入对齐（合并前处理新结果）。"""
    for item in manifest["files"]:
        if item["kind"] != "frontend":
            continue
        logical = item["path"]
        path = Path(logical)
        if path.name != "data.ts" or "views" not in path.parts:
            continue
        target = root / logical
        if not target.exists():
            continue
        target.write_text(
            apply_column_align(target.read_text(encoding="utf-8"), categories),
            encoding="utf-8")


_RANGE_LINE = re.compile(r"模块\s+(\w+)\s+错误码区间\s+\[(\d+(?:-\d+)+)\s*~")


def error_code_segment_start(boot: Path, module: str) -> int:
    """从 ServiceErrorCodeRange 的区间注释读取模块段首。"""
    matches = list(boot.rglob("ServiceErrorCodeRange.java"))
    if len(matches) != 1:
        raise ConfigError("ServiceErrorCodeRange.java 未找到或不止一份")
    found = {name: int(start.replace("-", ""))
             for name, start in _RANGE_LINE.findall(matches[0].read_text(encoding="utf-8"))}
    if module not in found:
        raise ConfigError(f"模块未登记错误码区间: {module}")
    return found[module]


def _constants_source(config: ProjectConfig, module: str) -> str:
    return (
        f"package {config.base_package}.module.{module}.enums;\n\n"
        "public interface ErrorCodeConstants {\n}\n"
    )


def apply_error_codes(boot: Path, manifest: dict, workdir: Path, config: ProjectConfig,
                      dry_run: bool) -> None:
    """把错误码合并到模块常量文件。已登记才写入。"""
    module = manifest["moduleName"]
    manual = next((workdir / item["path"] for item in manifest["files"]
                   if item["kind"] == "manual"), None)
    errors_file = workdir / "error-codes.json"
    if manual is None and not errors_file.exists():
        return
    if errors_file.exists():
        entries = json.loads(errors_file.read_text(encoding="utf-8"))
    else:
        entries = [{"name": match.group(1), "message": match.group(2)}
                   for match in ERROR_CODE.finditer(manual.read_text(encoding="utf-8"))]
    targets = list(boot.glob(
        f"{config.backend_path_prefix}{module}/src/main/java/**/enums/ErrorCodeConstants.java"))
    if targets:
        target = targets[0]
        source = target.read_text(encoding="utf-8")
    else:
        package_path = Path(*config.base_package.split(".")) / "module" / module / "enums"
        target = (boot / f"{config.backend_path_prefix}{module}" / "src/main/java"
                  / package_path / "ErrorCodeConstants.java")
        source = _constants_source(config, module)
    existing = set(re.findall(r"ErrorCode\s+(\w+)\s*=", source))
    for entry in entries:
        if entry["name"] in existing:
            print(f"skip error code {entry['name']}")
    fresh = [entry for entry in entries if entry["name"] not in existing]
    if not fresh:
        return
    used = [int(value.replace("_", "")) for value in re.findall(r"new ErrorCode\((\d[\d_]*)", source)]
    start_bound = error_code_segment_start(boot, module)
    start = max(used) + 1 if used else start_bound
    merged = merge_error_code_entries(source, fresh, start)
    merged = ensure_error_code_import(merged, config.base_package)
    if dry_run:
        print(f"merge error codes -> {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(merged, encoding="utf-8")


def _mysql_command(host: str, user: str, database: str,
                   docker_container: str | None, extra: list[str] | None = None) -> list[str]:
    """构造 mysql 命令；Docker 模式走容器 socket。"""
    password = os.environ.get("MYSQL_PWD", "")
    command: list[str]
    if docker_container:
        command = ["docker", "exec", "-i"]
        if password:
            command.extend(["-e", f"MYSQL_PWD={password}"])
        command.extend([docker_container, "mysql", "--default-character-set=utf8mb4",
                        "-u", user, database])
    else:
        command = ["mysql", "--default-character-set=utf8mb4", "-h", host, "-u", user, database]
    if extra:
        command.extend(extra)
    return command


def _query(sql: str, host: str, user: str, database: str,
           docker_container: str | None) -> str | None:
    """执行只读查询；不可用时返回 None。"""
    env = dict(os.environ, MYSQL_PWD=os.environ.get("MYSQL_PWD", ""))
    try:
        result = subprocess.run(
            _mysql_command(host, user, database, docker_container, ["-N", "-B", "-e", sql]),
            capture_output=True, text=True, check=True, env=env)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def query_menu_max(host: str, user: str, database: str,
                   docker_container: str | None, table: str = "system_menu") -> int | None:
    value = _query(f"SELECT COALESCE(MAX(id), 0) FROM `{table}`", host, user, database,
                   docker_container)
    return int(value) if value and value.isdigit() else None


def query_menu_max_in_segment(host: str, user: str, database: str,
                              docker_container: str | None, table: str,
                              base: int, upper: int) -> int | None:
    """只查号段内的最大菜单 id；段外历史 id 不参与取号。"""
    value = _query(
        f"SELECT COALESCE(MAX(id), 0) FROM `{table}` WHERE id >= {base} AND id < {upper}",
        host, user, database, docker_container)
    return int(value) if value and value.isdigit() else None


def next_menu_start(local_start: int, db_max: int | None, base: int, upper: int) -> int:
    """把数据库段内最大值并入起点；段外 db_max 忽略。"""
    if db_max is not None and base <= db_max < upper:
        return max(local_start, db_max + 1)
    return local_start


def query_menu_id(host: str, user: str, database: str,
                  docker_container: str | None, path: str, name: str,
                  table: str = "system_menu") -> int | None:
    """与 find_menu_id 相同：绝对 path 只比 path；相对 path 比 path+name。"""
    safe_path = path.replace("'", "''")
    safe_name = name.replace("'", "''")
    if path.startswith("/"):
        sql = f"SELECT id FROM `{table}` WHERE path = '{safe_path}' LIMIT 1"
    else:
        sql = (f"SELECT id FROM `{table}` WHERE path = '{safe_path}' "
               f"AND name = '{safe_name}' LIMIT 1")
    value = _query(sql, host, user, database, docker_container)
    return int(value) if value and value.isdigit() else None


def apply_upgrade(upgrade: Path, host: str, user: str, database: str,
                  docker_container: str | None = None) -> None:
    """执行增量 SQL；本机无 mysql 时可用 Docker 容器。"""
    command = _mysql_command(host, user, database, docker_container)
    with upgrade.open("rb") as stdin:
        subprocess.run(command, stdin=stdin, check=True, env=os.environ)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--ddl", action="append", type=Path, default=[])
    parser.add_argument("--apply-sql", action="store_true")
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-user", default="root")
    parser.add_argument("--db-name")
    parser.add_argument("--menu-start-id", type=int)
    parser.add_argument("--docker-container")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--menu-decision", type=Path)
    parser.add_argument("--dict-decision", type=Path)
    parser.add_argument("--column-categories", type=Path)
    args = parser.parse_args()

    try:
        config = load_project_config(Path.cwd())
    except ConfigError as error:
        print(f"配置错误：{error}")
        print("请参考 ~/.agents/skills/f-base-codegen-mcp/config.example.json")
        return 2
    workdir = args.zip.with_suffix("")
    manifest = load_bundle(args.zip, workdir)
    validate_manifest_module(manifest)
    ensure_module_scaffold(
        config, manifest["moduleName"], args.dry_run,
        tenant=bool(manifest.get("tenantEnabled")),
        export=bool(manifest.get("exportEnable", True)))
    workspace = Path.cwd()
    state_path = workspace / ".tmp" / "f-base-codegen-state.json"
    state = load_state(state_path)
    # 后处理先落在解压出的新结果上，再参与合并与基线保存
    if args.column_categories is not None:
        categories = json.loads(args.column_categories.read_text(encoding="utf-8"))
        apply_column_align_sources(workdir, manifest, categories)
    if not args.dry_run:
        # 枚举/TODO 只认 --dict-decision；缺省跳过，不按 ZIP dicts 猜测
        maybe_apply_dict_decision(config, manifest, workdir, args.dict_decision)
    copied = copy_sources(
        manifest, workdir, config, args.dry_run, args.force, state, workspace=workspace)
    upgrade = apply_sql(config, manifest, workdir, args.ddl, args.dry_run,
                        args.menu_start_id, args.db_host, args.db_user,
                        args.db_name, args.docker_container,
                        args.menu_decision, args.dict_decision)
    apply_error_codes(config.boot_root, manifest, workdir, config, args.dry_run)
    if not args.dry_run:
        save_state(state_path, copied)
    if args.apply_sql and upgrade is not None:
        if not args.db_name:
            parser.error("--apply-sql 需要 --db-name")
        apply_upgrade(upgrade, args.db_host, args.db_user, args.db_name,
                      args.docker_container)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
