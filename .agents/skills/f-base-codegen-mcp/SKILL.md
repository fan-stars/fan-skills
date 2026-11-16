---
name: f-base-codegen-mcp
description: Use when a database table should become base CRUD through a remote Streamable HTTP MCP, or when a codegen ZIP must be applied to a configured boot and Vben workspace.
disable-model-invocation: false
---

# 基础类生成（远程 MCP）

## 适用范围

用于把数据库表生成 boot/vben 基础 CRUD 类。只使用远程 MCP 的 **Streamable HTTP `/mcp`** 接口；不启动本地 MCP，不访问 `/sse`，不回退旧 fan-mcp 工具名。

## 前置检查（必须先做）

以下命令都在**工作区根目录**执行；脚本从当前目录读取 `scripts/config/f-base-codegen-mcp.json`。

在写任何文件前：

1. 调用 `current_time`，确认 MCP 可达；若返回 discovery/auth 错误，先让用户完成 MCP 客户端认证（如 `mcp_auth`），再重试。
2. 确认 `codegen_bundle`、`codegen_list`、`codegen_detail`、`codegen_update`、`codegen_capabilities` 可用。
3. 读取工作区 `scripts/config/f-base-codegen-mcp.json`。
4. 校验 `basePackage`、`bootRoot`、`vbenRoot`、`sqlDir`。
5. 若配置了 `sqlRulesPath`，校验文件存在、`sql-id-segments` JSON 含必需键且可解析。

任一项失败：**停止**，不生成代码、不写 SQL，并提示用户配置 Streamable HTTP MCP：

```json
{
  "mcpServers": {
    "fan-mcp": {
      "url": "https://your-host/mcp",
      "headers": { "X-Mcp-Key": "<key>" }
    }
  }
}
```

配置示例见 [config.example.json](config.example.json)，字段说明见 [reference.md](reference.md)。

## 工具面

只使用这 14 个工具，全部串行调用：

```text
current_time
dict_by_type
menu_by_id
codegen_list
codegen_detail
codegen_db_tables
codegen_import
codegen_update
codegen_sync
codegen_preview
codegen_create_table
codegen_bundle
codegen_alter_table
codegen_capabilities
```

不要调用旧工具名：`getCodegenTablePage`、`getCodegenDetail`、`downloadCodegen`、`getSimpleMenuList` 等。

## 执行流程

1. `codegen_list` 按 `pageReqVO.tableName` 查表。
2. 未导入时用 `codegen_db_tables` 找数据源，`codegen_import` 导入。
3. `codegen_detail` 读取表 + 字段。
4. 建表/改表前调用 `codegen_capabilities`，确认 scopes 包含 `ddl:create_table` / `ddl:alter_table`；缺失时停止，不使用猜测。
5. `codegen_update` 配置 moduleName、businessName、className、classComment、parentMenuId、frontType、字段查询/字典/宽度。`moduleName` 必须显式配置，不能从表名前缀推断；示例表使用 `demo_*`。
   - 树表：`templateType=2`，设置 `treeParentColumnId`、`treeNameColumnId`，父列启用 create/update。
   - 主子表：主表 `templateType=12`，子表 `15`，设置 `masterTableId`、`subJoinColumnId`、`subJoinMany`；关联列按需隐藏。
6. 需要改表时使用 `codegen_alter_table(tableId, sql)`；只允许 `ADD`、`MODIFY`、`CHANGE` 和单独的表 `RENAME TO`，禁止 `DROP` 子句和多语句。表重命名只更新物理表名和 `codegen.tableName`，不改类名、业务名、菜单和路由。
7. `codegen_bundle(tableId, basePackage)` 获取 ZIP。
8. 本地运行：

```bash
python3 ~/.agents/skills/f-base-codegen-mcp/scripts/apply_bundle.py \
  --zip .tmp/codegen.zip --ddl .tmp/schema.sql --dry-run
```

主子表每个表都给一个 `--ddl`（可重复）；脚本会合并全部 DDL。首次应用后会在 `.tmp/f-base-codegen-state.json` 记录源/目标哈希；同一 ZIP 重跑自动跳过。目标文件被人工改动或来源变化时停止，确认后可加 `--force`。

确认目标清单后去掉 `--dry-run` 执行。

9. 读本地 SQL：父菜单、字典、DDL。
10. 基线 SQL + `sql/mysql/upgrade/` 增量 SQL 双写；无模块 SQL 时新建。增量文件名 `{date}-{moduleName}-{businessName}`，`businessName` 中 `/` 换成 `-`；重名时依次追加 `-2`、`-3`…。`parentMenuId` 不写入 `menu.plan.json`。父菜单先在本地 SQL 中按 path/name 查找；没有则新建一级菜单，同一条父菜单 INSERT 同时写入基线与增量。菜单多条 INSERT 之间不留空行。
11. 补常量/枚举，合并错误码；常量文件已存在就合并，包括空接口；不存在且模块已登记错误码区间就新建。没有数字时首码取 ServiceErrorCodeRange 里该模块的段首。未登记则不写入编号。同名跳过并在标准输出报告名字。手工文件名保持 ErrorCodeConstants_手动操作.java。
12. 只执行增量 SQL；菜单编号按 `sqlRulesPath` 号段取号，需要时用 `--menu-start-id` / `menuStartId` 抬高（不得越过段上界）；本机无 mysql 时使用 `--docker-container mysql8`，密码通过 `docker exec -e MYSQL_PWD=...` 传入；构建 boot/vben 并报告结果。

## 包名与配置

包名不写死：

1. 配置 `basePackage`（已设置则不读 yaml）；
2. 否则用 `basePackageKey` 在 `applicationConfig` 指向的 yaml 里取包名；
3. 都没有则停止。

- MCP 数据源由客户端 `X-Mcp-DataSource` 请求头决定；项目配置不保存数据源编号。
- 无请求头时由 MCP 使用默认数据源；密钥未分配默认数据源时工具调用会失败。
- MCP 库和本地开发库是两套环境：MCP 后续独立部署，不要求库名/实例一致；本地 SQL 只执行到项目开发库。
- 配置 `sqlRulesPath` 时，模块必须已登记在 `modules`；JSON 缺失/非法、模块未登记或号段用尽时停止写入。未配置时回退全局最大编号 +1 并提示。
- 密钥表里的“无数据源”实际是“仅默认数据源 0”，不是 `[]`。
- 显式传 `dataSourceConfigId` 时必须等于当前 `X-Mcp-DataSource` 上下文，否则拒绝。
- 表重命名只影响物理表名和 `codegen.tableName`；独立本地库需要单独执行本地 `RENAME TO` 并更新 SQL。

路径前缀、SQL 前缀、frontType、构建命令都来自配置。

## 安全与幂等

- 不覆盖人工修改；冲突先报告。
- 同一份 ZIP 重复应用必须幂等。
- 建表/改表前先查 `codegen_capabilities`；示例表使用 `demo_*`，默认库系统表保护不可绕过。
- 菜单记录合并到 `moduleName` 对应的 `{sqlModulePrefix}{module}.sql`（默认 `fan-module-`）；文件不存在时新建。
- Job 种子行统一在 `fan-module-infra.sql`：`infra_job` 的 DDL 与全部 job 行都在该文件；跨模块 handler（如 system 的 `TokenCleanJob`）在行上方注释标注；job id 按 handler 所属模块号段，`QRTZ_*`/`infra_job_log` 不写种子行。
- 技能当前不写 job 行；不要从 `infra_job` 反推或自动生成 job。
- 菜单编号按 `sqlRulesPath` 的模块号段取号：段内 `{sqlModulePrefix}*.sql` 最大编号 +1，传 `--db-name` 时并入目标库同段最大值；`--menu-start-id` / `menuStartId` 只作下限，不得 ≥ 段上界。未配置时回退全局最大编号 +1，并提示未使用号段规则。
- 父菜单先查 SQL/数据库；没有则创建一级菜单，不写死 `/system`。
- 导入/建表后必须 `codegen_update` 显式设置 `moduleName`；`demo` 是合法模块，不做特殊拦截。
- 按 `moduleScaffold` 建骨架：`parent`、`jar`、已配置的 starter、根 pom 的 `<module>` 行、server 依赖（不写 version）、BOM 里带 `${revision}` 的登记，以及调用 `openApiMethod` 的 `*WebConfiguration`。模块 pom.xml 已存在则不改；只有目录或扁平构建文件时补齐缺失的 pom、分组配置、空错误码接口和三处登记；已有源文件和已有登记行不覆盖。缺键脚本停止。不需要改服务端 `module-names`，也不需要重启 MCP。
- `moduleName=demo` 合法，不特殊拦截。
- 主子表旧文件先删除再重新生成，避免同一 package 下重复类。
- 父菜单按 bundle 的 `menu.plan.parent.path` 解析；查不到时新建一级菜单，不写死 `/system`。
- `codegen_alter_table` 后直接 `codegen_detail`；只有物理表被库外修改时才 `codegen_sync`。
- MCP 库和项目库可以独立，不能假设一致。
- bundle 前校验主键 `id.updateOperation` 为开启；树表父字段必须保留增改操作。
- 不提供删除表、删除生成物或清理元数据。
- 不把 MCP 密钥写进仓库或配置。
- 不查远程菜单/字典库；本地 SQL 是权威。
- 生成代码后先改 SQL，再执行增量。

## 参考

- [reference.md](reference.md)：配置字段、14 工具参数、路径/SQL/枚举规则。
- [GAPS.md](GAPS.md)：已知缺口。记录本身不改变本技能的执行步骤。
- `scripts/project_config.py`：配置读取。
- `scripts/apply_bundle.py`：落盘、SQL、枚举、错误码。
- `tests/`：脚本测试。
