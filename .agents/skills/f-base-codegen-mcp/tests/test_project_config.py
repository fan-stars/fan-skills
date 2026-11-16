import json
import sys
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.project_config import ConfigError, enum_reference, load_project_config


class TestProjectConfig(unittest.TestCase):

    def test_missing_config_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ConfigError):
                load_project_config(Path(tmp))

    def test_base_package_falls_back_to_application_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            config_dir = workspace / "scripts" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "f-base-codegen-mcp.json").write_text(
                json.dumps({
                    "bootRoot": "fan-base",
                    "vbenRoot": "fan-base-vben",
                    "frontendPathPrefix": "fan-base-vben/",
                    "frontendAppRoot": "apps/web-antd/src",
                    "backendPathPrefix": "fan-module-",
                    "sqlDir": "fan-base/sql/mysql",
                    "sqlModulePrefix": "fan-module-",
                }),
                encoding="utf-8",
            )
            app = workspace / "fan-base" / "fan-server" / "src/main/resources"
            app.mkdir(parents=True)
            (app / "application.yaml").write_text(
                "yudao:\n  info:\n    base-package: cn.fanstars\n",
                encoding="utf-8",
            )

            config = load_project_config(workspace)

            self.assertEqual(config.base_package, "cn.fanstars")
            self.assertEqual(config.boot_root, workspace / "fan-base")
            self.assertEqual(config.frontend_path_prefix, "fan-base-vben/")

    def test_enum_placeholder_uses_base_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            config_dir = workspace / "scripts" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "f-base-codegen-mcp.json").write_text(
                json.dumps({
                    "basePackage": "cn.fanstars",
                    "bootRoot": "fan-base",
                    "vbenRoot": "fan-base-vben",
                    "frontendPathPrefix": "fan-base-vben/",
                    "backendPathPrefix": "fan-module-",
                    "sqlDir": "fan-base/sql/mysql",
                    "sqlModulePrefix": "fan-module-",
                    "enums": {
                        "common_status": "{basePackage}.framework.common.enums.CommonStatusEnum"
                    },
                }),
                encoding="utf-8",
            )
            config = load_project_config(workspace)
            self.assertEqual(
                enum_reference(config, "common_status"),
                "cn.fanstars.framework.common.enums.CommonStatusEnum",
            )
            self.assertIsNone(enum_reference(config, "unknown_dict"))

    def test_sql_rules_path_is_loaded(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "scripts/config").mkdir(parents=True)
            (workspace / "scripts/config/f-base-codegen-mcp.json").write_text(
                json.dumps({
                    "basePackage": "cn.iocoder.yudao",
                    "bootRoot": "boot",
                    "vbenRoot": "vben",
                    "frontendPathPrefix": "vben/",
                    "backendPathPrefix": "module-",
                    "sqlDir": "sql",
                    "sqlModulePrefix": "module-",
                    "sqlRulesPath": "sql/README.md",
                }),
                encoding="utf-8",
            )
            config = load_project_config(workspace)
            self.assertEqual(config.sql_rules_path, workspace / "sql/README.md")

    def test_sql_rules_path_defaults_to_none(self) -> None:
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "scripts/config").mkdir(parents=True)
            (workspace / "scripts/config/f-base-codegen-mcp.json").write_text(
                json.dumps({
                    "basePackage": "cn.iocoder.yudao",
                    "bootRoot": "boot",
                    "vbenRoot": "vben",
                    "frontendPathPrefix": "vben/",
                    "backendPathPrefix": "module-",
                    "sqlDir": "sql",
                    "sqlModulePrefix": "module-",
                }),
                encoding="utf-8",
            )
            config = load_project_config(workspace)
            self.assertIsNone(config.sql_rules_path)


if __name__ == "__main__":
    unittest.main()
