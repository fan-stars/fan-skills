# 参考：配置、工具与落地规则

## 配置文件

`scripts/config/f-base-codegen-mcp.json`

| 字段 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `basePackage` | 否 | 从 application.yaml 读取 | Java 基础包；已配置时不读 yaml |
| `basePackageKey` | 否 | `base-package` | yaml 里包名属性路径（点分隔全路径或叶子键名） |
| `applicationConfig` | 否 | boot 下自动查找 | 供 `basePackageKey` 读取包名的 application.yaml |
| `bootRoot` | 是 | 无 | 后端仓库目录 |
| `vbenRoot` | 是 | 无 | 前端仓库目录 |
| `frontType` | 否 | `40` | Vben5 Ant Design |
| `backendPathPrefix` | 是 | 无 | 清单后端路径前缀 |
| `frontendPathPrefix` | 是 | 无 | 清单前端路径前缀 |
| `frontendAppRoot` | 否 | `apps/web-antd/src` | 前端子应用 src |
| `sqlDir` | 是 | 无 | 模块 SQL 目录 |
| `sqlModulePrefix` | 是 | 无 | 模块 SQL 文件名前缀 |
| `sqlRulesPath` | 否 | 无 | SQL 规则文件路径（含 `sql-id-segments` JSON），配置后按模块号段取号 |
| `moduleScaffold` | 否 | 无 | 新模块骨架：`rootPom`、`serverPom`、`bomPom`、`groupId`、`parentArtifactId`、`openApiMethod`、`starters`、`tenantStarter`、`excelStarter`；模块 pom.xml 已存在则不改；只有目录或扁平构建文件时补齐缺失的 pom、分组配置、空错误码接口和三处登记；已有源文件和已有登记行不覆盖；缺键停止 |
| `sqlPrelude` | 是 | 无 | 新模块 SQL 头注释里的前置文件列表，按顺序执行 |
| `menuTable` | 否 | `system_menu` | 菜单表名 |
| `menuStartId` | 否 | 无 | 菜单起始编号下限；配置 `sqlRulesPath` 时不得越过模块段上界 |
| `parentMenuPath` | 否 | 无 | 父菜单路径；缺省使用 bundle/模块路径，不写死 `/system` |
| `enums` | 否 | `{}` | 已有字典类型 → 已有枚举全名对照表（不是列名规则），支持 `{basePackage}`；只写进 Javadoc `{@link}` |
| `build.boot` | 否 | 无 | 后端构建命令 |
| `build.vben` | 否 | 无 | 前端构建命令 |

配置 `sqlRulesPath` 时，模块必须已登记在 `modules`；JSON 缺失/非法、模块未登记或号段用尽时停止写入。

配置文件不能保存 MCP 密钥。

## 工具参数

| 工具 | 参数 |
|---|---|
| `current_time` | 无 |
| `codegen_list` | `pageReqVO: {pageNo, pageSize, tableName}` |
| `codegen_db_tables` | `name?, comment?`；数据源来自当前上下文 |
| `codegen_import` | `author, reqVO: {tableNames}`；数据源来自当前上下文 |
| `codegen_detail` | `tableId` |
| `codegen_update` | `reqVO: {table, columns}`，整表保存 |
| `codegen_sync` | `tableId` |
| `codegen_create_table` | `sql, author`；数据源来自当前上下文 |
| `codegen_alter_table` | `tableId, sql`；改表语句必须匹配当前数据源表 |
| `codegen_capabilities` | 无参数；返回当前密钥 scopes、数据源编号和当前数据源 |

`codegen_db_tables` / `codegen_import` / `codegen_create_table` / `codegen_alter_table` 的 `dataSourceConfigId` 是可选参数；传入时必须等于当前 `X-Mcp-DataSource` 上下文，否则拒绝。
| `codegen_preview` | `tableId, basePackage?, tenantEnabled?` |
| `codegen_bundle` | `tableId, basePackage?, tenantEnabled?`；表必须属于当前数据源 |
| `menu_by_id` | `id` |
| `dict_by_type` | `dictType` |

`codegen_bundle` 返回 `text + resource`；ZIP 含 `manifest.json`、源码、`menu.plan.json`、`error-codes.json`、`menu.reference.sql`。

## 数据源

- MCP 客户端通过 `X-Mcp-DataSource` 选择数据源；项目配置不保存数据源编号。
- 无请求头使用默认数据源；密钥未分配默认数据源时工具调用失败。
- 默认数据源禁止 CREATE/ALTER 系统表；非默认数据源允许，但仍禁止 DROP 子句和多语句。
- 表重命名只更新物理表名和 `codegen.tableName`，不改类名、菜单、路由。

## 路径映射

后端：

```text
{bootRoot}/{backendPathPrefix}{module}/... 
```

前端：

```text
{vbenRoot}/{frontendAppRoot}/{去掉 frontendPathPrefix 和 src/ 的剩余路径}
```

示例表名使用 `demo_*`，不得用 `system_*` 作为默认库示例。

路径示例：

```text
{vbenRoot}/src/views/demo/demo/index.vue
→ {vbenRoot}/apps/web-antd/src/views/demo/demo/index.vue
```

`frontendPathPrefix` 与 `vbenRoot` 独立：逻辑前缀不一定等于实际仓库目录。

## 密钥语义

| 场景 | scopes | 数据源 |
|---|---|---|
| 全能力 | create + alter | 通常 `[0]` 或更多 |
| 仅建表 | create | `[0]` |
| 仅改表 | alter | `[0]` |
| 仅默认源 | 按需 | `[0]`，不是 `[]` |

“无数据源”是误称；空列表创建时归一化为默认源 `0`。

## 多 key 探测

Cursor 一次只能配置一把 key。需要比较多把 key 时，用工作区 `scripts/mcp-test/lib/mcp_client.py` 直连 `/mcp`，只在命令行临时传 key，不写入仓库。

## 能力查询

- 建表/改表前调用 `codegen_capabilities`；
- 缺工具、查询失败或缺 `ddl:create_table` / `ddl:alter_table` 时停止；
- 不接受 keyId 参数，不能猜测。

## 三种表配置

### 单表

- `templateType=1`
- 默认就是单表。存在 `parent_id`、`*_id` 或看起来像子表时仍然是单表，除非用户这次明确说了树表或主子表。
- `columnComment` 是列表标题、搜索标签、表单标签和 Java 注释，只写短句。
- `colWidth` 写入 schema 列表的 `minWidth`。展示列写整数。不展示的列在 `codegen_update` 里显式传 null。省略时模板使用 120。

### 树表

仅当用户这次明确说了树表。
- `templateType=2`
- `treeParentColumnId`：`parent_id` 列 id
- `treeNameColumnId`：名称列 id
- `moduleName` 由 `codegen_update` 显式设置；`demo` 是合法模块。
- 按 `moduleScaffold` 建模块 pom、`ErrorCodeConstants`、`*WebConfiguration`，并写入根 pom、server pom（无 version）、BOM（`${revision}`）；模块 pom.xml 已存在则不改；只有目录或扁平构建文件时补齐缺失的 pom、分组配置、空错误码接口和三处登记；已有源文件和已有登记行不覆盖；缺键停止；不改服务端白名单、不重启 MCP。
- `moduleName=demo` 是合法值。
- 父列必须启用 `createOperation` / `updateOperation`，否则 Service 会调用不存在的 `getParentId()`。
- `codegen_bundle` 前校验：父列增改为 true；否则不要下载，先修配置。

### 主子表

仅当用户这次明确说了主子表。
- 主表：`templateType=12`（内嵌）/ `10` / `11`
- 子表：`templateType=15`
- 子表：`masterTableId`、`subJoinColumnId`、`subJoinMany=true`
- 外键列通常不参与 create/update/list 条件。
- `codegen_bundle` 只返回主表 manifest 元数据；子表源码会包含，但 DDL、字典、错误码需按子表补齐。
- 每个表都传 `--ddl`：`--ddl master.sql --ddl sub.sql`。

## SQL

- 基线：`{sqlDir}/{sqlModulePrefix}{module}.sql`。
- 增量：`{sqlDir}/upgrade/{date}-{moduleName}-{businessName}.sql`；`businessName` 中 `/` 换成 `-`；重名追加 `-2`、`-3`…。
- 基线不包含 `DROP`；删表语句写入 `{sqlDir}/fan-drop.sql` 的注释态清单。
- 增量使用 `CREATE TABLE IF NOT EXISTS`，不带 `DROP`；脚本会删除所有 `DROP TABLE IF EXISTS` 并对全部 `CREATE TABLE` 加 `IF NOT EXISTS`。
- 读取 `sqlRulesPath` 的 `sql-id-segments` JSON 块，菜单编号按模块号段取号。
- 新表 `AUTO_INCREMENT` 统一为 10001；没有自增列时不改写。
- 删表清单只写 `-- DROP TABLE IF EXISTS` 注释行，不生成可执行 DROP。
- 增量脚本随其变更归档时删除；技能写入的脚本在归档前保留。
- `infra_job` 的 DDL 和全部 job 种子行都在 `fan-module-infra.sql`；跨模块 handler（如 system 的 `TokenCleanJob`）在行上方注释标注；job id 按 handler 所属模块号段分配，运行期自增 100001。
- `QRTZ_*`、`infra_job_log` 不写种子行；`TokenCleanJob` 用 id 1，infra 的 3 个清理 job 用 2001–2003。
- 技能当前不写 `infra_job` 行；job 行由模块 SQL 手工维护，直到 codegen bundle 增加 job 元数据。
- 菜单/按钮：显式 ID、全列、`b'1'`、`CURRENT_TIMESTAMP`。
- 配置 `sqlRulesPath` 时：取该模块号段 `[base, upper)` 内 `fan*.sql` 已用最大编号 +1；传入 `--db-name` 时并入目标库同段最大值；`--menu-start-id` / `menuStartId` 只作下限，不得 ≥ 段上界。模块未登记、规则缺失或号段用尽时停止写入。
- 未配置 `sqlRulesPath` 时：回退所有 `{sqlModulePrefix}*.sql` 全局最大编号 +1；传入 `--db-name` 时查全局 `MAX(id)`，并提示未使用号段规则。
- `parentMenuId` 不进 `menu.plan.json`；父菜单按 path/name 先查本地 SQL，再查数据库；都没有时创建一级菜单，同一条父 INSERT 写入基线与增量；多条菜单 INSERT 之间不留空行；不写死 `/system`。
- 菜单合并到 `{sqlModulePrefix}{module}.sql`（默认 `fan-module-`）；文件不存在时新建最小骨架。
- 字典：`--dict-decision` 的 `creates` 写入 `system_dict_type` / `system_dict_data` INSERT（两表各自段内最大编号 +1）；枚举与 TODO 也以该结论文件为唯一输入。菜单按 id 有序插入 `menuTable` 记录段，不追加到末尾。
- 多行菜单 INSERT 必须能解析；解析失败直接报错，不默认生成 1。
- 父菜单从本地 SQL 解析；单层挂模块根，多级建目录；不唯一时询问。
- 按菜单名称/路径/组件检查重复；重复应用输出 `already applied`。
- 只执行增量 SQL，不重跑基线。
- 本机无 mysql 时使用 `--docker-container <容器名>`；Docker 模式走容器 socket，密码通过 `docker exec -e MYSQL_PWD=...` 传入。

```bash
docker exec -i -e MYSQL_PWD="$MYSQL_PWD" mysql8 \
  mysql --default-character-set=utf8mb4 -uroot fan_jdk25_mcp < upgrade.sql
```

## 前端 API 的 Dayjs 导入（技能后处理）

- 生成模板会无条件写入 `import type { Dayjs } from 'dayjs';`（`vue3_vben5_ele/schema/api/api.ts.vm`；antd 只 `#parse`）。**不改模板**，由技能在 `apply_bundle` 落盘后收尾。
- 处理对象：本次写入的 `apps/web-antd`（或配置的前端根）下对应业务 API `.ts`。
- 判定：文件中若存在 `| Dayjs` 或字段类型 `: Dayjs`（含 `string | Dayjs`），保留 import；否则删除整行 `import type { Dayjs } from 'dayjs';`（含前后空行只留一处合理空白）。
- 日期列范围与模板一致：Java 类型为 `date` / `LocalDate` / `LocalDateTime` 且出现在 create 或 update 契约中时才会用到 `Dayjs`。
- 实现位置：后续可做成 `apply_bundle` 的确定性后处理函数；在此之前由执行技能的 Agent 按上列规则手工改落盘文件并纳入基线。

## 枚举与字典结论

- `dict-decision.json`（`--dict-decision`）是建枚举、消字典 TODO、补前端 `dict-enum.ts` 键的**唯一**输入；不以 ZIP `dicts` 猜常量名，也不写字符串形式的 `@DictFormat("…")`。
- 未传 `--dict-decision` 时：跳过枚举与 TODO 处理（不猜测、不落盘常量/枚举）；技能流程在 `apply_bundle` 前必须写好 `.tmp/dict-decision.json` 并传入该参数。SQL 字典 INSERT 同样只认该文件的 `creates`。
- `enums` 是「已有字典类型 → 已有枚举全名」对照表，不是列名规则；`{basePackage}` 替换为配置包名。绑定且对照表有类名时：`{@link TODO}` 换成该类名，`@DictFormat` 改成 `DictTypeConstants` 常量并补模块 import；对照表没有类名则停止，不编类名。
- 配置示例把 `common_status` 接到 `CommonStatusEnum`，把 `system_user_sex` 接到 `SexEnum`；类型链接只写完整类名，不向业务模块 import 另一个业务模块的枚举。
- `create`：按结论常量名在 `{basePackage}.module.{module}.enums.{首段}` 新建枚举（数字 → `ArrayValuable<Integer>`；非数字 → `String` 且无该接口）；常量名用结论中的大写标识符，不因值 `1` 命名为 `DISABLE`；并在前端 `packages/constants/src/dict-enum.ts` 的 `{MODULE}_DICT` 分组补同名键（已存在则跳过）。
- Javadoc 链接写完整类名，例如 `{@link cn.fanstars.framework.common.enums.CommonStatusEnum}`。
- 字典类型与字典数据 INSERT 编号分别按各自表段内最大值加 1。

## 改表

- 只允许 `ADD`、`MODIFY`、`CHANGE` 和单独的表 `RENAME TO`；
- `DROP` 子句、RENAME 与其他子句混用、多语句、库名限定均拒绝；
- 表重命名后先更新元数据 `tableName`，再同步字段；元数据失败不回滚物理表；
- 独立本地库需再执行本地 `RENAME TO` 并更新 SQL。

## 错误码

- 优先读取 `error-codes.json`；缺失时回退到 `ErrorCodeConstants_手动操作.java`。
- 合并到 `{backendPathPrefix}{module}/src/main/java/**/enums/ErrorCodeConstants.java`。
- 常量文件已存在就合并，包括空接口；不存在且模块已登记错误码区间就新建。没有数字时首码取 ServiceErrorCodeRange 里该模块的段首。未登记则不写入编号。同名跳过并在标准输出报告名字。手工文件名保持 ErrorCodeConstants_手动操作.java。
- 只做本地文件合并，不依赖远程库。

## 失败处理

| 场景 | 行为 |
|---|---|
| 没有 MCP | 停止，给 `mcpServers` 示例 |
| 缺 `codegen_bundle` | 停止，说明 MCP 版本不支持 |
| 缺 `codegen_capabilities` / 查询失败 | 停止 DDL，说明 MCP 版本或能力查询失败 |
| 缺配置 | 停止，给 `config.example.json` |
| 包名非法 | 停止，要求修正 |
| 不可见表/表不存在 | 停止，不生成 |
| ZIP 超限 | 停止，不落盘 |
| SQL/菜单冲突 | 停止该写入，报告冲突 |
| 构建失败 | 保留文件，报告失败命令 |
