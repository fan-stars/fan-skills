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


def copy_sources(manifest: dict, workdir: Path, config: ProjectConfig,
                 dry_run: bool, force: bool = False, state: dict | None = None) -> list[tuple[Path, Path]]:
    """复制源码；相同内容幂等，人工改动默认冲突。"""
    copied = []
    state = state or {}
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
        content = source_path.read_text(encoding="utf-8")
        if target.exists():
            target_text = target.read_text(encoding="utf-8")
            entry = state.get(str(target)) or {}
            same_source = entry.get("source") == _sha256(source_path)
            same_target = entry.get("target") == _sha256(target)
            if target_text != content and not (same_source and same_target) and not force:
                raise FileConflict(
                    f"target changed: {target} (use --force to overwrite)")
        if dry_run:
            print(f"{logical} -> {target}")
            copied.append((source_path, target))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        copied.append((source_path, target))
    return copied


def find_menu_id(sql: str, path: str, name: str, table: str = "system_menu") -> int | None:
    """按 path 或 name 查找菜单编号。"""
    pattern = re.compile(
        r"INSERT INTO `" + re.escape(table)
        + r"` .*?VALUES \((\d+), '([^']*)', '([^']*)', (\d+), (\d+), (\d+), '([^']*)'", re.S
    )
    for match in pattern.finditer(sql):
        if match.group(7) == path or match.group(2) == name:
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


def _constant_name(value: str) -> str:
    if value == "0":
        return "ENABLE"
    if value == "1":
        return "DISABLE"
    return "VALUE_" + re.sub(r"\W+", "_", value).upper()


def create_enum_file(boot: Path, base_package: str, module: str, dict_type: str,
                     values: list[tuple[str, str]], module_dir: str | None = None) -> Path:
    """按字典值创建枚举类。"""
    enum_name = _pascal(dict_type) + "Enum"
    domain = dict_type.split("_")[0]
    java_type = "Integer" if all(value.isdigit() for value, _ in values) else "String"
    lines = [
        f"package {base_package}.module.{module}.enums.{domain};",
        "",
        "import lombok.AllArgsConstructor;",
        "import lombok.Getter;",
        "",
        "/**",
        f" * {dict_type} 枚举。",
        " */",
        "@Getter",
        "@AllArgsConstructor",
        f"public enum {enum_name} {{",
        "",
    ]
    body = []
    for value, label in values:
        literal = value if java_type == "Integer" else f'"{value}"'
        body.append(f'    {_constant_name(value)}({literal}, "{label}")')
    lines.append(",\n".join(body) + ";")
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
        "<project>\n"
        "    <parent>\n"
        f"        <groupId>{group_id}</groupId>\n"
        f"        <artifactId>{parent_artifact_id}</artifactId>\n"
        "        <version>${revision}</version>\n"
        "    </parent>\n"
        f"    <artifactId>{artifact_id}</artifactId>\n"
        "    <packaging>jar</packaging>\n"
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
              docker_container: str | None = None) -> Path | None:
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
    if not (new_ddl or menu_sql):
        print("already applied")
        return None
    if menu_sql:
        sql = insert_menu_rows(sql, menu_sql, config.menu_table)
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


def resolve_known_enums(boot: Path, manifest: dict, config: ProjectConfig) -> None:
    """把配置中已知字典的 TODO 换成完整枚举类名。"""
    for item in manifest["files"]:
        if item["kind"] != "backend" or not item["path"].endswith(".java"):
            continue
        target = boot / item["path"]
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        for dict_type in config.enums:
            reference = enum_reference(config, dict_type)
            if not reference:
                continue
            text = text.replace(f"TODO {dict_type} 对应的类", reference)
            text = text.replace(
                f'@DictFormat("{dict_type}") // TODO 代码优化：建议设置到对应的 DictTypeConstants 枚举类中',
                f'@DictFormat("{dict_type}")',
            )
        target.write_text(text, encoding="utf-8")


def apply_dicts(boot: Path, manifest: dict, config: ProjectConfig) -> None:
    """按生成包用到的字典补常量/枚举，并替换 TODO。"""
    module = manifest["moduleName"]
    sql_text = "\n".join(path.read_text(encoding="utf-8")
                         for path in config.sql_dir.glob(f"{config.sql_module_prefix}*.sql"))
    for item in manifest.get("dicts", []):
        dict_type = item["dictType"]
        if enum_reference(config, dict_type):
            continue
        values = parse_dict_values(sql_text, dict_type)
        if not values:
            ensure_dict_constant(config, module, dict_type)
            continue
        enum_path = create_enum_file(boot, config.base_package, module, dict_type, values,
                                     config.backend_path_prefix + module)
        enum_ref = (f"{config.base_package}.module.{module}.enums."
                    f"{dict_type.split('_')[0]}.{enum_path.stem}")
        ensure_dict_constant(config, module, dict_type)
        for file in manifest["files"]:
            if file["kind"] != "backend" or not file["path"].endswith(".java"):
                continue
            target = boot / file["path"]
            if not target.exists():
                continue
            text = target.read_text(encoding="utf-8")
            text = text.replace(f"TODO {dict_type} 对应的类", enum_ref)
            text = text.replace(
                f'@DictFormat("{dict_type}") // TODO 代码优化：建议设置到对应的 DictTypeConstants 枚举类中',
                f'@DictFormat("{dict_type}")',
            )
            target.write_text(text, encoding="utf-8")


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
    safe_path = path.replace("'", "''")
    safe_name = name.replace("'", "''")
    value = _query(
        f"SELECT id FROM `{table}` WHERE path = '{safe_path}' OR name = '{safe_name}' LIMIT 1",
        host, user, database, docker_container)
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
    state_path = Path.cwd() / ".tmp" / "f-base-codegen-state.json"
    state = load_state(state_path)
    copied = copy_sources(manifest, workdir, config, args.dry_run, args.force, state)
    if not args.dry_run:
        resolve_known_enums(config.boot_root, manifest, config)
        apply_dicts(config.boot_root, manifest, config)
    upgrade = apply_sql(config, manifest, workdir, args.ddl, args.dry_run,
                        args.menu_start_id, args.db_host, args.db_user,
                        args.db_name, args.docker_container)
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
