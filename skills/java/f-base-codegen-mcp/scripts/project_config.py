from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_RELATIVE = Path("scripts/config/f-base-codegen-mcp.json")
PACKAGE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")


class ConfigError(RuntimeError):
    pass


@dataclass
class ProjectConfig:
    base_package: str
    boot_root: Path
    vben_root: Path
    frontend_path_prefix: str
    frontend_app_root: str
    backend_path_prefix: str
    sql_dir: Path
    sql_module_prefix: str
    menu_table: str
    parent_menu_path: str
    front_type: int = 40
    menu_start_id: int | None = None
    module_scaffold: dict = field(default_factory=dict)
    enums: dict[str, str] = field(default_factory=dict)
    build: dict[str, str] = field(default_factory=dict)
    sql_rules_path: Path | None = None
    sql_prelude: list[str] = field(default_factory=list)


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"missing config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _find_base_package(config_path: Path | None, boot_root: Path,
                       key: str | None = None) -> str:
    leaf = (key or "base-package").split(".")[-1]
    pattern = re.compile(rf"^\s*{re.escape(leaf)}:\s*(\S+)\s*$", re.M)
    candidates = []
    if config_path:
        candidates.append(config_path)
    candidates.extend(sorted(boot_root.glob("*/src/main/resources/application.yaml")))
    for path in candidates:
        if not path.exists():
            continue
        match = pattern.search(path.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    raise ConfigError("basePackage not found in config or application.yaml")


def _required(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not value:
        raise ConfigError(f"missing config field: {key}")
    return value


def load_project_config(workspace: Path) -> ProjectConfig:
    raw = _read_json(workspace / CONFIG_RELATIVE)
    boot_root = workspace / _required(raw, "bootRoot")
    vben_root = workspace / _required(raw, "vbenRoot")
    app_config = raw.get("applicationConfig")
    app_config_path = workspace / app_config if app_config else None
    base_package = raw.get("basePackage") or _find_base_package(
        app_config_path, boot_root, raw.get("basePackageKey"))
    if not PACKAGE_PATTERN.fullmatch(base_package):
        raise ConfigError(f"invalid basePackage: {base_package}")
    rules_value = raw.get("sqlRulesPath")
    sql_rules_path = workspace / rules_value if rules_value else None
    return ProjectConfig(
        base_package=base_package,
        boot_root=boot_root,
        vben_root=vben_root,
        frontend_path_prefix=_required(raw, "frontendPathPrefix"),
        frontend_app_root=raw.get("frontendAppRoot", "apps/web-antd/src"),
        backend_path_prefix=_required(raw, "backendPathPrefix"),
        sql_dir=workspace / _required(raw, "sqlDir"),
        sql_module_prefix=_required(raw, "sqlModulePrefix"),
        menu_table=raw.get("menuTable", "system_menu"),
        parent_menu_path=raw.get("parentMenuPath", ""),
        front_type=raw.get("frontType", 40),
        menu_start_id=raw.get("menuStartId"),
        module_scaffold=raw.get("moduleScaffold", {}),
        enums=raw.get("enums", {}),
        build=raw.get("build", {}),
        sql_rules_path=sql_rules_path,
        sql_prelude=list(raw.get("sqlPrelude") or []),
    )


def enum_reference(config: ProjectConfig, dict_type: str) -> str | None:
    template = config.enums.get(dict_type)
    return template.replace("{basePackage}", config.base_package) if template else None
