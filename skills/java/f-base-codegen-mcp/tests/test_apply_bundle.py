import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.apply_bundle import (
    FileConflict,
    apply_error_codes,
    apply_sql,
    copy_sources,
    create_enum_file,
    ensure_dict_constant,
    ensure_parent_menu,
    insert_table_ddl,
    map_backend_path,
    map_frontend_path,
    merge_error_code_entries,
    merge_error_codes,
    module_sql_path,
    next_menu_id,
    ensure_module_scaffold,
    validate_manifest_module,
    parse_dict_values,
    upgrade_ddl,
)
from scripts.project_config import ProjectConfig


def make_config() -> ProjectConfig:
    return ProjectConfig(
        base_package="cn.fanstars",
        boot_root=Path("/repo/fan-base"),
        vben_root=Path("/repo/fan-base-vben"),
        frontend_path_prefix="fan-base-vben/",
        frontend_app_root="apps/web-antd/src",
        backend_path_prefix="fan-module-",
        sql_dir=Path("/repo/fan-base/sql/mysql"),
        sql_module_prefix="fan-module-",
        menu_table="system_menu",
        parent_menu_path="/system",
        sql_prelude=["drop.sql", "module-system.sql"],
    )


class TestApplyBundle(unittest.TestCase):

    def test_front_type_40_maps_configured_app_root(self) -> None:
        target = map_frontend_path(
            "fan-base-vben/src/views/system/demo/index.vue", 40, make_config())
        self.assertEqual(
            target,
            Path("/repo/fan-base-vben/apps/web-antd/src/views/system/demo/index.vue"),
        )

    def test_backend_path_keeps_module_under_boot_root(self) -> None:
        target = map_backend_path(
            "fan-module-system/src/main/java/Demo.java", make_config())
        self.assertEqual(
            target,
            Path("/repo/fan-base/fan-module-system/src/main/java/Demo.java"),
        )

    def test_sql_path_uses_configured_prefix(self) -> None:
        self.assertEqual(
            module_sql_path(make_config(), "system"),
            Path("/repo/fan-base/sql/mysql/fan-module-system.sql"),
        )

    def test_next_menu_id_uses_max(self) -> None:
        sql = "INSERT INTO `system_menu` (`id`) VALUES (152, 'x');"
        self.assertEqual(next_menu_id(sql), 153)

    def test_apply_sql_creates_missing_module_sql(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            config.sql_dir = root / "sql"
            config.sql_dir.mkdir()
            workdir = root / "bundle"
            workdir.mkdir()
            ddl = root / "demo.sql"
            ddl.write_text("CREATE TABLE `demo_ex_single` (id bigint);", encoding="utf-8")
            manifest = {"moduleName": "system", "businessName": "exsingle",
                        "tableName": "demo_ex_single"}
            apply_sql(config, manifest, workdir, [ddl], False)
            module_sql = config.sql_dir / "fan-module-system.sql"
            self.assertTrue(module_sql.exists())
            self.assertIn("demo_ex_single", module_sql.read_text(encoding="utf-8"))

    def test_manifest_module_demo_is_valid(self) -> None:
        validate_manifest_module({"moduleName": "demo"})

    def test_insert_table_ddl_keeps_alphabetical_order(self) -> None:
        sql = (
            "-- Table structure for system_login_log\n"
            "CREATE TABLE `system_login_log` (id bigint);\n"
            "-- Table structure for system_menu\n"
            "CREATE TABLE `system_menu` (id bigint);\n"
        )
        updated = insert_table_ddl(
            sql,
            "system_mcp_flow_demo",
            "-- Table structure for system_mcp_flow_demo\nCREATE TABLE `system_mcp_flow_demo` (id bigint);",
        )
        self.assertLess(
            updated.index("system_mcp_flow_demo"),
            updated.index("-- Table structure for system_menu"),
        )

    def test_ensure_parent_creates_root_menu(self) -> None:
        sql = "SET FOREIGN_KEY_CHECKS = 0;\nSET FOREIGN_KEY_CHECKS = 1;"
        updated, parent_id, _created = ensure_parent_menu(
            sql, {"name": "系统管理", "path": "/system", "icon": "ep:menu"})
        self.assertIn("'系统管理'", updated)
        self.assertIn("'/system'", updated)
        self.assertEqual(parent_id, 1)

    def test_ensure_parent_uses_segment(self) -> None:
        rules = (
            "<!-- sql-id-segments:start -->\n```json\n"
            '{"nextModuleBase": 50, "modules": {"system": 1},\n'
            ' "autoIncrement": {"default": 10001, "shared": {}}}\n'
            "```\n<!-- sql-id-segments:end -->\n"
        )
        with TemporaryDirectory() as tmp:
            rules_path = Path(tmp) / "README.md"
            rules_path.write_text(rules, encoding="utf-8")
            config = make_config()
            config.sql_rules_path = rules_path
            sql = ("-- ----------------------------\n-- Records of system_menu\n"
                   "-- ----------------------------\nBEGIN;\n"
                   "INSERT INTO `system_menu` (`id`, `name`) VALUES (1, 'a');\n"
                   "INSERT INTO `system_menu` (`id`, `name`) VALUES (2, 'b');\n"
                   "INSERT INTO `system_menu` (`id`, `name`) VALUES (3, 'c');\n"
                   "COMMIT;\n")
            parent = {"path": "/pay", "name": "支付", "icon": "ep:money"}
            updated, parent_id, _created = ensure_parent_menu(sql, parent, config, "system")
            self.assertEqual(parent_id, 4)
            self.assertIn("VALUES (4,", updated)
            extended = (sql + "INSERT INTO `system_menu` (`id`, `name`) "
                        "VALUES (13480, 'legacy');\n")
            updated, parent_id, _created = ensure_parent_menu(extended, parent, config, "system")
            self.assertEqual(parent_id, 4)
            self.assertIn("VALUES (4,", updated)

    def test_ensure_parent_merges_db_max_inside_segment(self) -> None:
        rules = (
            "<!-- sql-id-segments:start -->\n```json\n"
            '{"nextModuleBase": 200, "modules": {"demo": 50},\n'
            ' "autoIncrement": {"default": 10001, "shared": {}}}\n'
            "```\n<!-- sql-id-segments:end -->\n"
        )
        with TemporaryDirectory() as tmp:
            rules_path = Path(tmp) / "README.md"
            rules_path.write_text(rules, encoding="utf-8")
            config = make_config()
            config.sql_rules_path = rules_path
            sql = "INSERT INTO `system_menu` (`id`, `name`) VALUES (50, 'a');\n"
            parent = {"path": "/demo", "name": "示例", "icon": "ep:menu"}
            _updated, parent_id, _created = ensure_parent_menu(
                sql, parent, config, "demo", db_max=80)
            self.assertEqual(parent_id, 81)
            _updated, parent_id, _created = ensure_parent_menu(
                sql, parent, config, "demo", db_max=None)
            self.assertEqual(parent_id, 51)

    def test_parse_dict_values(self) -> None:
        sql = (
            "INSERT INTO `system_dict_data` (`id`, `sort`, `label`, `value`, `dict_type`) VALUES "
            "(90, 1, '开启', '0', 'mcp_flow_status');\n"
            "INSERT INTO `system_dict_data` (`id`, `sort`, `label`, `value`, `dict_type`) VALUES "
            "(91, 2, '关闭', '1', 'mcp_flow_status');"
        )
        self.assertEqual(parse_dict_values(sql, "mcp_flow_status"), [("0", "开启"), ("1", "关闭")])

    def test_create_enum_file_uses_base_package(self) -> None:
        with TemporaryDirectory() as tmp:
            path = create_enum_file(Path(tmp), "cn.fanstars", "system", "mcp_flow_status",
                                    [("0", "开启"), ("1", "关闭")])
            text = path.read_text(encoding="utf-8")
            self.assertIn("package cn.fanstars.module.system.enums.mcp;", text)
            self.assertIn("enum McpFlowStatusEnum", text)
            self.assertIn("ENABLE(0, \"开启\")", text)

    def test_insert_table_ddl_adds_semicolon(self) -> None:
        sql = "-- Table structure for system_menu\nCREATE TABLE `system_menu` (id bigint);\n"
        updated = insert_table_ddl(sql, "system_demo", "CREATE TABLE `system_demo` (id bigint)")
        self.assertIn("CREATE TABLE `system_demo` (id bigint);", updated)

    def test_ensure_auto_increment_replaces_and_adds(self) -> None:
        from scripts.apply_bundle import ensure_auto_increment
        replaced = ensure_auto_increment(
            "CREATE TABLE `t` (`id` bigint NOT NULL AUTO_INCREMENT) ENGINE = InnoDB AUTO_INCREMENT = 7;")
        self.assertIn("AUTO_INCREMENT = 10001", replaced)
        added = ensure_auto_increment(
            "CREATE TABLE `t` (`id` bigint NOT NULL AUTO_INCREMENT) ENGINE = InnoDB;")
        self.assertIn("ENGINE = InnoDB AUTO_INCREMENT = 10001", added)

    def test_insert_table_ddl_has_no_records_comment(self) -> None:
        sql = "-- Table structure for a\nCREATE TABLE `a` (`id` bigint);\n"
        updated = insert_table_ddl(sql, "b", "CREATE TABLE `b` (`id` bigint NOT NULL AUTO_INCREMENT);")
        self.assertNotIn("-- Records of b", updated)
        self.assertIn("AUTO_INCREMENT = 10001", updated)

    def test_insert_menu_rows_keeps_order_and_creates_block(self) -> None:
        from scripts.apply_bundle import insert_menu_rows
        sql = ("-- ----------------------------\n-- Records of system_menu\n"
               "-- ----------------------------\nBEGIN;\n"
               "INSERT INTO `system_menu` (`id`, `name`) VALUES (1, 'a');\nCOMMIT;\n")
        row = "INSERT INTO `system_menu` (`id`, `name`) VALUES (2, 'b');"
        updated = insert_menu_rows(sql, [row], "system_menu")
        self.assertLess(updated.index("VALUES (1,"), updated.index("VALUES (2,"))
        created = insert_menu_rows("SET FOREIGN_KEY_CHECKS = 0;\n\n-- 恢复外键检查\nSET FOREIGN_KEY_CHECKS = 1;\n",
                                   [row], "system_menu")
        self.assertIn("-- Records of system_menu", created)
        self.assertIn("BEGIN;", created)

    def test_new_module_sql_uses_section_layout(self) -> None:
        from scripts.apply_bundle import new_module_sql
        text = new_module_sql("pay", ["drop.sql", "module-system.sql"])
        self.assertIn("SET NAMES utf8mb4;", text)
        self.assertIn("-- 关闭外键检查", text)
        self.assertIn("-- 恢复外键检查", text)
        self.assertIn("SET FOREIGN_KEY_CHECKS = 1;", text)

    def test_append_drop_tables_is_commented(self) -> None:
        from scripts.apply_bundle import append_drop_tables
        with TemporaryDirectory() as tmp:
            sql_dir = Path(tmp)
            (sql_dir / "fan-drop.sql").write_text(
                "-- 恢复外键检查\nSET FOREIGN_KEY_CHECKS = 1;\n", encoding="utf-8")
            append_drop_tables(sql_dir, "pay", ["pay_order"])
            text = (sql_dir / "fan-drop.sql").read_text(encoding="utf-8")
            self.assertIn("-- pay 模块", text)
            self.assertIn("-- DROP TABLE IF EXISTS `pay_order`;", text)
            self.assertNotIn("\nDROP TABLE", text)

    def test_next_menu_start_ignores_out_of_segment(self) -> None:
        from scripts.apply_bundle import next_menu_start
        self.assertEqual(next_menu_start(4, 13493, 1, 50), 4)
        self.assertEqual(next_menu_start(4, 60, 1, 50), 4)
        self.assertEqual(next_menu_start(4, 10, 1, 50), 11)

    def test_insert_table_ddl_strips_drop_and_comment(self) -> None:
        sql = "-- Table structure for a\nCREATE TABLE `a` (`id` bigint);\n"
        ddl = "-- copied\nDROP TABLE IF EXISTS `b`;\nCREATE TABLE `b` (`id` bigint NOT NULL AUTO_INCREMENT);"
        updated = insert_table_ddl(sql, "b", ddl)
        self.assertNotIn("DROP TABLE", updated)
        self.assertEqual(updated.count("-- Table structure for b"), 1)
        with self.assertRaises(ValueError):
            insert_table_ddl(updated, "b", ddl)

    def test_insert_menu_rows_multiline(self) -> None:
        from scripts.apply_bundle import insert_menu_rows
        sql = ("-- ----------------------------\n-- Records of system_menu\n"
               "-- ----------------------------\nBEGIN;\n"
               "INSERT INTO `system_menu` (`id`, `name`)\nVALUES (1, 'a');\nCOMMIT;\n")
        row = "INSERT INTO `system_menu` (`id`, `name`) VALUES (2, 'b');"
        updated = insert_menu_rows(sql, [row])
        self.assertEqual(updated.count("-- Records of system_menu"), 1)
        self.assertLess(updated.index("VALUES (1,"), updated.index("VALUES (2,"))

    def test_append_drop_tables_existing_group(self) -> None:
        from scripts.apply_bundle import append_drop_tables
        with TemporaryDirectory() as tmp:
            sql_dir = Path(tmp)
            (sql_dir / "fan-drop.sql").write_text(
                "-- ----------------------------\n-- pay 模块\n-- ----------------------------\n"
                "-- DROP TABLE IF EXISTS `pay_old`;\n\n-- 恢复外键检查\nSET FOREIGN_KEY_CHECKS = 1;\n",
                encoding="utf-8")
            append_drop_tables(sql_dir, "pay", ["pay_new"])
            text = (sql_dir / "fan-drop.sql").read_text(encoding="utf-8")
            self.assertIn("-- DROP TABLE IF EXISTS `pay_new`;", text)
            self.assertEqual(text.count("-- pay 模块"), 1)

    def test_upgrade_ddl_removes_drop_and_all_create(self) -> None:
        ddl = ("DROP TABLE IF EXISTS `a`;\nCREATE TABLE `a` (id bigint);\n"
               "DROP TABLE IF EXISTS `b`;\nCREATE TABLE `b` (id bigint);")
        upgraded = upgrade_ddl(ddl)
        self.assertNotIn("DROP TABLE", upgraded)
        self.assertEqual(upgraded.count("CREATE TABLE IF NOT EXISTS"), 2)

    def test_next_menu_id_handles_multiline_insert(self) -> None:
        sql = ("INSERT INTO `system_menu` (`id`, `name`)\nVALUES (152, 'x');\n")
        self.assertEqual(next_menu_id(sql), 153)

    def test_ensure_dict_constant_creates_missing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            config = make_config()
            config.boot_root = Path(tmp)
            ensure_dict_constant(config, "system", "mcp_flow_status")
            path = (Path(tmp) / "fan-module-system/src/main/java/cn/fanstars/module/system/enums"
                    / "DictTypeConstants.java")
            self.assertIn("MCP_FLOW_STATUS", path.read_text(encoding="utf-8"))

    def test_apply_sql_supports_master_and_sub_ddl(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            config.sql_dir = root / "sql"
            config.sql_dir.mkdir()
            module_sql = config.sql_dir / "fan-module-system.sql"
            module_sql.write_text("SET FOREIGN_KEY_CHECKS = 0;\nSET FOREIGN_KEY_CHECKS = 1;",
                                  encoding="utf-8")
            workdir = root / "bundle"
            workdir.mkdir()
            master = root / "master.sql"
            master.write_text("DROP TABLE IF EXISTS `system_cg_master`;\n"
                              "CREATE TABLE `system_cg_master` (id bigint);", encoding="utf-8")
            sub = root / "sub.sql"
            sub.write_text("CREATE TABLE `system_cg_sub` (id bigint);", encoding="utf-8")
            manifest = {"moduleName": "system", "businessName": "cgmaster",
                        "tableName": "system_cg_master"}

            upgrade = apply_sql(config, manifest, workdir, [master, sub], False)

            self.assertIsNotNone(upgrade)
            base = module_sql.read_text(encoding="utf-8")
            self.assertIn("system_cg_master", base)
            self.assertIn("system_cg_sub", base)
            text = upgrade.read_text(encoding="utf-8")
            self.assertNotIn("DROP TABLE", text)
            self.assertEqual(text.count("CREATE TABLE IF NOT EXISTS"), 2)

    def test_copy_sources_rejects_changed_target(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            workdir = root / "bundle"
            config = make_config()
            config.boot_root = root / "repo"
            source = workdir / "fan-module-system/src/main/java/Demo.java"
            source.parent.mkdir(parents=True)
            source.write_text("new", encoding="utf-8")
            target = config.boot_root / "fan-module-system/src/main/java/Demo.java"
            target.parent.mkdir(parents=True)
            target.write_text("manual", encoding="utf-8")
            manifest = {"frontType": 40, "files": [
                {"kind": "backend", "path": "fan-module-system/src/main/java/Demo.java"}]}
            with self.assertRaises(FileConflict):
                copy_sources(manifest, workdir, config, dry_run=False)

    def test_apply_error_codes_reads_json_bundle(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 system 错误码区间 [1-002-000-000 ~ 1-003-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "NEW_CODE", "message": "新增"}]', encoding="utf-8")
            target = (config.boot_root / "fan-module-system/src/main/java/cn/fanstars/module/system/enums"
                      / "ErrorCodeConstants.java")
            target.parent.mkdir(parents=True)
            target.write_text(
                "public class ErrorCodeConstants {\n"
                "    ErrorCode OLD = new ErrorCode(1_002_030_000, \"旧\");\n}\n",
                encoding="utf-8")
            apply_error_codes(config.boot_root, {"moduleName": "system", "files": []},
                              workdir, config, dry_run=False)
            text = target.read_text(encoding="utf-8")
            self.assertIn("NEW_CODE", text)
            self.assertIn("1_002_030_001", text)

    def test_merge_error_code_entries_from_json(self) -> None:
        source = "    ErrorCode OLD = new ErrorCode(1_002_030_000, \"旧\");\n}"
        merged = merge_error_code_entries(source, [{"name": "NEW", "message": "新增"}],
                                          1_002_030_001)
        self.assertIn("NEW", merged)
        self.assertIn("1_002_030_001", merged)

    def test_merge_error_codes_skips_duplicate_and_appends_new(self) -> None:
        source = (
            "    ErrorCode DEMO_EXISTS = new ErrorCode(1_002_030_000, \"已存在\");\n"
            "    // 其他常量\n}"
        )
        manual = (
            "    ErrorCode DEMO_EXISTS = new ErrorCode(TODO 补充编号, \"已存在\");\n"
            "    ErrorCode DEMO_NEW = new ErrorCode(TODO 补充编号, \"新增\");\n"
        )
        updated = merge_error_codes(source, manual, 1_002_030_000)
        self.assertEqual(updated.count("DEMO_EXISTS"), 1)
        self.assertIn("DEMO_NEW", updated)
        self.assertIn("1_002_030_001", updated)

    def test_upgrade_ddl_sets_auto_increment(self) -> None:
        text = upgrade_ddl(
            "DROP TABLE IF EXISTS `t`;\n"
            "CREATE TABLE `t` (`id` bigint NOT NULL AUTO_INCREMENT) AUTO_INCREMENT = 7;")
        self.assertNotIn("DROP TABLE", text)
        self.assertIn("CREATE TABLE IF NOT EXISTS", text)
        self.assertIn("AUTO_INCREMENT = 10001", text)

    def test_insert_table_ddl_keeps_section_borders(self) -> None:
        sql = (
            "-- ----------------------------\n"
            "-- Table structure for a\n"
            "-- ----------------------------\n"
            "CREATE TABLE `a` (`id` bigint);\n\n"
            "-- ----------------------------\n"
            "-- Records of a\n"
            "-- ----------------------------\n"
            "BEGIN;\nINSERT INTO `a` (`id`) VALUES (1);\nCOMMIT;\n\n"
            "-- 恢复外键检查\nSET FOREIGN_KEY_CHECKS = 1;\n"
        )
        after_records = insert_table_ddl(
            sql, "b", "CREATE TABLE `b` (`id` bigint NOT NULL AUTO_INCREMENT);")
        before_marker = insert_table_ddl(
            sql, "0", "CREATE TABLE `0` (`id` bigint NOT NULL AUTO_INCREMENT);")
        for updated in (after_records, before_marker):
            self.assertNotIn("-- ----------------------------\n-- ----------------------------", updated)
            self.assertEqual(updated.count("-- ----------------------------"), 6)
            self.assertEqual(updated.count("-- Table structure for a"), 1)
            self.assertEqual(updated.count("-- Records of a"), 1)

    def test_append_drop_tables_existing_group_keeps_order(self) -> None:
        from scripts.apply_bundle import append_drop_tables
        with TemporaryDirectory() as tmp:
            sql_dir = Path(tmp)
            (sql_dir / "fan-drop.sql").write_text(
                "-- ----------------------------\n-- pay 模块\n-- ----------------------------\n"
                "-- DROP TABLE IF EXISTS `pay_zzz`;\n\n-- 恢复外键检查\nSET FOREIGN_KEY_CHECKS = 1;\n",
                encoding="utf-8")
            append_drop_tables(sql_dir, "pay", ["pay_aaa"])
            text = (sql_dir / "fan-drop.sql").read_text(encoding="utf-8")
            self.assertEqual(text.count("-- DROP TABLE IF EXISTS"), 2)
            self.assertLess(text.index("pay_zzz"), text.index("pay_aaa"))

    def test_new_module_sql_uses_configured_prelude(self) -> None:
        from scripts.apply_bundle import new_module_sql
        text = new_module_sql("pay", ["drop.sql", "module-system.sql", "module-infra.sql"])
        self.assertIn("drop.sql → module-system.sql → module-infra.sql → 本文件", text)

    def test_new_module_sql_rejects_empty_prelude(self) -> None:
        from scripts.apply_bundle import new_module_sql
        from scripts.project_config import ConfigError
        with self.assertRaises(ConfigError):
            new_module_sql("pay", [])

    def test_upgrade_includes_new_parent_without_blank_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.sql_prelude = ["drop.sql", "module-system.sql"]
            config.boot_root = root / "repo"
            config.sql_dir = root / "sql"
            config.sql_dir.mkdir()
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "menu.plan.json").write_text(
                '{"parent":{"name":"demo","path":"/demo","icon":"ep:menu"},'
                '"menu":{"name":"卡片管理","path":"card","component":"demo/card/index",'
                '"componentName":"Card","type":2,"sort":0,"icon":"ep:document"},'
                '"buttons":[{"name":"卡片查询","permission":"demo:card:query","type":3,"sort":1}]}',
                encoding="utf-8")
            ddl = root / "demo.sql"
            ddl.write_text("CREATE TABLE `demo_phone_card` (id bigint);", encoding="utf-8")
            upgrade = apply_sql(config, {"moduleName": "demo", "businessName": "phone"},
                                workdir, [ddl], False)
            text = upgrade.read_text(encoding="utf-8")
            self.assertIn("'/demo'", text)
            self.assertIn("'卡片管理'", text)
            self.assertNotRegex(text, r"INSERT INTO `system_menu`[^;]*;\n\nINSERT INTO `system_menu`")
            base = (config.sql_dir / "fan-module-demo.sql").read_text(encoding="utf-8")
            self.assertIn("'/demo'", base)

    def test_upgrade_parent_id_follows_aggregated_menu_ids(self) -> None:
        import re
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.sql_rules_path = None
            config.boot_root = root / "repo"
            config.sql_dir = root / "sql"
            config.sql_dir.mkdir()
            (config.sql_dir / "fan-module-system.sql").write_text(
                "INSERT INTO `system_menu` (`id`, `name`) VALUES (1, '系统管理');\n"
                "INSERT INTO `system_menu` (`id`, `name`) VALUES (3005, '已有菜单');\n",
                encoding="utf-8")
            (config.sql_dir / "fan-module-infra.sql").write_text(
                "SET NAMES utf8mb4;\n", encoding="utf-8")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "menu.plan.json").write_text(
                '{"parent":{"name":"demo","path":"/demo","icon":"ep:menu"},'
                '"menu":{"name":"卡片管理","path":"card","component":"demo/card/index",'
                '"componentName":"Card","type":2,"sort":0,"icon":"ep:document"},'
                '"buttons":[{"name":"卡片查询","permission":"demo:card:query","type":3,"sort":1}]}',
                encoding="utf-8")
            ddl = root / "demo.sql"
            ddl.write_text("CREATE TABLE `demo_phone_card` (id bigint);", encoding="utf-8")
            upgrade = apply_sql(config, {"moduleName": "demo", "businessName": "phone"},
                                workdir, [ddl], False)
            text = upgrade.read_text(encoding="utf-8")
            rows = re.findall(
                r"INSERT INTO `system_menu` .*?VALUES \((\d+), '([^']*)', '([^']*)', "
                r"(\d+), (\d+), (\d+), '([^']*)'",
                text, re.S)
            parent_id = int(next(row[0] for row in rows if row[6] == "/demo"))
            self.assertGreater(parent_id, 3005)
            self.assertNotEqual(parent_id, 1)
            child_ids = [int(row[0]) for row in rows if int(row[0]) != parent_id]
            self.assertTrue(child_ids)
            for child_id in child_ids:
                self.assertGreater(child_id, parent_id)
                self.assertNotEqual(child_id, 1)

    def scaffold_config(self) -> dict:
        return {
            "rootPom": "pom.xml",
            "serverPom": "server/pom.xml",
            "bomPom": "bom/pom.xml",
            "groupId": "com.example",
            "parentArtifactId": "example-parent",
            "openApiMethod": "com.example.swagger.ExampleOpenApi.buildGroupedOpenApi",
            "starters": ["example-starter-mybatis", "example-starter-security"],
            "tenantStarter": "example-starter-tenant",
            "excelStarter": "example-starter-excel",
        }

    def test_scaffold_writes_bom_and_openapi_without_server_version(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.base_package = "com.example"
            config.module_scaffold = self.scaffold_config()
            (root / "pom.xml").write_text("<project><modules>\n</modules></project>", encoding="utf-8")
            server = root / "server/pom.xml"
            server.parent.mkdir(parents=True)
            server.write_text("<project><dependencies>\n</dependencies></project>", encoding="utf-8")
            bom = root / "bom/pom.xml"
            bom.parent.mkdir(parents=True)
            bom.write_text(
                "<project><dependencyManagement><dependencies>\n"
                "</dependencies></dependencyManagement></project>", encoding="utf-8")
            ensure_module_scaffold(config, "demo", False, tenant=True, export=False)
            module_pom = (root / "fan-module-demo/pom.xml").read_text(encoding="utf-8")
            self.assertIn("example-starter-mybatis", module_pom)
            self.assertIn("example-starter-tenant", module_pom)
            self.assertNotIn("example-starter-excel", module_pom)
            self.assertNotIn("<version>", module_pom.split("<dependencies>")[1])
            server_text = server.read_text(encoding="utf-8")
            self.assertIn("<artifactId>fan-module-demo</artifactId>", server_text)
            self.assertNotIn("<version>", server_text)
            bom_text = bom.read_text(encoding="utf-8")
            self.assertIn("<artifactId>fan-module-demo</artifactId>", bom_text)
            self.assertIn("<version>${revision}</version>", bom_text)
            web = (root / "fan-module-demo/src/main/java/com/example/module/demo"
                   / "framework/web/config/DemoWebConfiguration.java")
            source = web.read_text(encoding="utf-8")
            self.assertIn('ExampleOpenApi.buildGroupedOpenApi("demo")', source)
            second = ensure_module_scaffold(config, "demo", False, tenant=True, export=True)
            self.assertFalse(second)
            self.assertNotIn("example-starter-excel",
                             (root / "fan-module-demo/pom.xml").read_text(encoding="utf-8"))

    def test_scaffold_stops_when_a_required_key_is_missing(self) -> None:
        from scripts.project_config import ConfigError
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.module_scaffold = {"rootPom": "pom.xml"}
            with self.assertRaises(ConfigError) as caught:
                ensure_module_scaffold(config, "demo", False)
            self.assertIn("serverPom", str(caught.exception))

    def write_range(self, boot: Path, body: str) -> None:
        path = boot / "range/ServiceErrorCodeRange.java"
        path.parent.mkdir(parents=True)
        path.write_text(body, encoding="utf-8")

    def test_apply_error_codes_numbers_empty_constants_from_range(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 demo 错误码区间 [1-009-000-000 ~ 1-010-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "CARD_NOT_EXISTS", "message": "不存在"}]', encoding="utf-8")
            target = (config.boot_root / "fan-module-demo/src/main/java/cn/fanstars/module/demo/enums"
                      / "ErrorCodeConstants.java")
            target.parent.mkdir(parents=True)
            target.write_text("public interface ErrorCodeConstants {\n}\n", encoding="utf-8")
            apply_error_codes(config.boot_root, {"moduleName": "demo", "files": []},
                              workdir, config, dry_run=False)
            text = target.read_text(encoding="utf-8")
            self.assertIn("CARD_NOT_EXISTS", text)
            self.assertIn("1_009_000_000", text)
            self.assertNotIn("1_002_030_000", text)

    def test_apply_error_codes_creates_missing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 demo 错误码区间 [1-009-000-000 ~ 1-010-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "CARD_NOT_EXISTS", "message": "不存在"}]', encoding="utf-8")
            apply_error_codes(config.boot_root, {"moduleName": "demo", "files": []},
                              workdir, config, dry_run=False)
            target = (config.boot_root / "fan-module-demo/src/main/java/cn/fanstars/module/demo/enums"
                      / "ErrorCodeConstants.java")
            text = target.read_text(encoding="utf-8")
            self.assertIn("package cn.fanstars.module.demo.enums;", text)
            self.assertIn("1_009_000_000", text)

    def test_apply_error_codes_keeps_empty_file_when_unregistered(self) -> None:
        from scripts.project_config import ConfigError
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 other 错误码区间 [1-009-000-000 ~ 1-010-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "CARD_NOT_EXISTS", "message": "不存在"}]', encoding="utf-8")
            target = (config.boot_root / "fan-module-demo/src/main/java/cn/fanstars/module/demo/enums"
                      / "ErrorCodeConstants.java")
            target.parent.mkdir(parents=True)
            original = "public interface ErrorCodeConstants {\n}\n"
            target.write_text(original, encoding="utf-8")
            with self.assertRaises(ConfigError):
                apply_error_codes(config.boot_root, {"moduleName": "demo", "files": []},
                                  workdir, config, dry_run=False)
            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_apply_error_codes_prefers_json_and_reports_duplicate(self) -> None:
        from io import StringIO
        from contextlib import redirect_stdout
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 demo 错误码区间 [1-009-000-000 ~ 1-010-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "CARD_NOT_EXISTS", "message": "不存在"}]', encoding="utf-8")
            manual = workdir / "ErrorCodeConstants_手动操作.java"
            manual.write_text(
                'ErrorCode ONLY_MANUAL = new ErrorCode(TODO 补充编号, "只在手工");\n',
                encoding="utf-8")
            target = (config.boot_root / "fan-module-demo/src/main/java/cn/fanstars/module/demo/enums"
                      / "ErrorCodeConstants.java")
            target.parent.mkdir(parents=True)
            target.write_text(
                "public interface ErrorCodeConstants {\n"
                "    ErrorCode CARD_NOT_EXISTS = new ErrorCode(1_009_000_000, \"不存在\");\n}\n",
                encoding="utf-8")
            manifest = {"moduleName": "demo", "files": [
                {"kind": "manual", "path": "ErrorCodeConstants_手动操作.java"}]}
            buffer = StringIO()
            with redirect_stdout(buffer):
                apply_error_codes(config.boot_root, manifest, workdir, config, dry_run=False)
            text = target.read_text(encoding="utf-8")
            self.assertNotIn("ONLY_MANUAL", text)
            self.assertEqual(manual.read_text(encoding="utf-8"),
                             'ErrorCode ONLY_MANUAL = new ErrorCode(TODO 补充编号, "只在手工");\n')
            self.assertIn("CARD_NOT_EXISTS", buffer.getvalue())

    def test_apply_error_codes_does_not_create_file_when_unregistered(self) -> None:
        from scripts.project_config import ConfigError
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root / "repo"
            self.write_range(
                config.boot_root,
                "// 模块 other 错误码区间 [1-009-000-000 ~ 1-010-000-000)\n")
            workdir = root / "bundle"
            workdir.mkdir()
            (workdir / "error-codes.json").write_text(
                '[{"name": "CARD_NOT_EXISTS", "message": "不存在"}]', encoding="utf-8")
            target = (config.boot_root / "fan-module-demo/src/main/java/cn/fanstars/module/demo/enums"
                      / "ErrorCodeConstants.java")
            with self.assertRaises(ConfigError):
                apply_error_codes(config.boot_root, {"moduleName": "demo", "files": []},
                                  workdir, config, dry_run=False)
            self.assertFalse(target.exists())

    def test_scaffold_fills_directory_that_only_has_flattened_pom(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.base_package = "com.example"
            config.module_scaffold = self.scaffold_config()
            module = root / "fan-module-demo"
            module.mkdir()
            (module / ".flattened-pom.xml").write_text("<flat/>", encoding="utf-8")
            (root / "pom.xml").write_text("<project><modules>\n</modules></project>", encoding="utf-8")
            server = root / "server/pom.xml"
            server.parent.mkdir(parents=True)
            server.write_text("<project><dependencies>\n</dependencies></project>", encoding="utf-8")
            bom = root / "bom/pom.xml"
            bom.parent.mkdir(parents=True)
            bom.write_text(
                "<project><dependencyManagement><dependencies>\n"
                "</dependencies></dependencyManagement></project>", encoding="utf-8")
            created = ensure_module_scaffold(config, "demo", False, tenant=False, export=False)
            self.assertTrue(created)
            self.assertTrue((module / "pom.xml").is_file())
            self.assertEqual((module / ".flattened-pom.xml").read_text(encoding="utf-8"), "<flat/>")
            self.assertIn("<artifactId>fan-module-demo</artifactId>", server.read_text(encoding="utf-8"))
            self.assertNotIn("example-starter-excel", (module / "pom.xml").read_text(encoding="utf-8"))

    def test_scaffold_does_not_overwrite_existing_pom(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.base_package = "com.example"
            config.module_scaffold = self.scaffold_config()
            module = root / "fan-module-demo"
            module.mkdir()
            (module / "pom.xml").write_text("<kept/>", encoding="utf-8")
            (root / "pom.xml").write_text("<project><modules>\n</modules></project>", encoding="utf-8")
            second = ensure_module_scaffold(config, "demo", False, tenant=False, export=True)
            self.assertFalse(second)
            self.assertEqual((module / "pom.xml").read_text(encoding="utf-8"), "<kept/>")

    def test_scaffold_stops_before_write_when_export_starter_missing(self) -> None:
        from scripts.project_config import ConfigError
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.base_package = "com.example"
            scaffold = self.scaffold_config()
            del scaffold["excelStarter"]
            config.module_scaffold = scaffold
            (root / "pom.xml").write_text("<project><modules>\n</modules></project>", encoding="utf-8")
            server = root / "server/pom.xml"
            server.parent.mkdir(parents=True)
            server.write_text("<project><dependencies>\n</dependencies></project>", encoding="utf-8")
            bom = root / "bom/pom.xml"
            bom.parent.mkdir(parents=True)
            bom.write_text(
                "<project><dependencyManagement><dependencies>\n"
                "</dependencies></dependencyManagement></project>", encoding="utf-8")
            with self.assertRaises(ConfigError) as caught:
                ensure_module_scaffold(config, "demo", False, tenant=False, export=True)
            self.assertIn("excelStarter", str(caught.exception))
            self.assertFalse((root / "fan-module-demo/pom.xml").exists())

    def test_scaffold_keeps_existing_sources_and_registration(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = make_config()
            config.boot_root = root
            config.base_package = "com.example"
            config.module_scaffold = self.scaffold_config()
            module = root / "fan-module-demo"
            enums = module / "src/main/java/com/example/module/demo/enums"
            enums.mkdir(parents=True)
            constants = enums / "ErrorCodeConstants.java"
            constants.write_text("public interface ErrorCodeConstants {\n}\n", encoding="utf-8")
            web = (module / "src/main/java/com/example/module/demo/framework/web/config"
                   / "DemoWebConfiguration.java")
            web.parent.mkdir(parents=True)
            web.write_text("class Kept {}\n", encoding="utf-8")
            (root / "pom.xml").write_text("<project><modules>\n</modules></project>", encoding="utf-8")
            server = root / "server/pom.xml"
            server.parent.mkdir(parents=True)
            server.write_text(
                "<project><dependencies>\n        <artifactId>fan-module-demo</artifactId>\n"
                "</dependencies></project>", encoding="utf-8")
            bom = root / "bom/pom.xml"
            bom.parent.mkdir(parents=True)
            bom.write_text(
                "<project><dependencyManagement><dependencies>\n"
                "</dependencies></dependencyManagement></project>", encoding="utf-8")
            created = ensure_module_scaffold(config, "demo", False, tenant=False, export=False)
            self.assertTrue(created)
            self.assertEqual(constants.read_text(encoding="utf-8"),
                             "public interface ErrorCodeConstants {\n}\n")
            self.assertEqual(web.read_text(encoding="utf-8"), "class Kept {}\n")
            self.assertEqual(server.read_text(encoding="utf-8").count("fan-module-demo"), 1)
            self.assertIn("<artifactId>fan-module-demo</artifactId>", bom.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
