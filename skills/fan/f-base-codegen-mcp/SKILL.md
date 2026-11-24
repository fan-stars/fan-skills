---
name: f-base-codegen-mcp
description: Use when generating boot or vben base CRUD from a database table with f-base-codegen-mcp, or when imported column comments, filters, list columns, forms, or list widths would stay on generator defaults.
disable-model-invocation: false
---

# 基础类生成（远程 MCP）

## 适用范围

用于把数据库表生成 boot/vben 基础 CRUD 类，并在导入后按 [prompts.md](prompts.md) 定稿列注释、字典、查询、列表、表单与列宽，避免沿用生成器默认值。只使用远程 MCP 的 **Streamable HTTP `/mcp`** 接口；不启动本地 MCP，不访问 `/sse`，不回退旧 fan-mcp 工具名。

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
5. 按 [prompts.md](prompts.md) 写十二份结论，顺序固定：注释、字典、查询、查询方式、显示类型、允许空、列表、插入、编辑、列宽、菜单、排序。除菜单外按详情列顺序一列一行。缺一份、漏一列、或出现「其余不要」，不调用 `codegen_update`。
6. 表类型默认 `templateType=1`。用户这次明确说了树表才用 `2`，明确说了主子表才用 `12`/`15`。有 `parent_id` 或 `*_id` 时仍然是单表。树表和主子表的列规则见 [reference.md](reference.md)。
7. 名字按 `sqlRulesPath` 指向的 SQL README 切段结果核对 `moduleName`、`businessName`、`className`。人点名要改的字段才覆盖。三字段由这次更新显式写入。核对后必须在对话里写出三个字段的当前值（即使与切段结果相同、即使未覆盖）。
8. 十二份都写全之后，调用一次 `codegen_update`。载荷包含详情里的每一列，以及表类型和三个名字。每一列带上排序步的 `ordinalPosition`。每列 `dictType` 只取自 `.tmp/dict-decision.json`（`bind`/`create` 写类型名，`none` 为空），不按列名或语义指定该绑哪个字典。`frontType` 仍用配置值。列表不展示的列把 `colWidth` 显式传 `null`。工具会丢掉 `null` 时停止。主键 `id` 的 `updateOperation` 保持 `true`。菜单结论写入 `.tmp/menu-decision.json`，列宽类别写入 `.tmp/column-categories.json`（键用 Java 属性名如 `createTime`，值是「编号 / 状态 / 时间 / 短名称 / 中等文本 / 长文本」）。字典结论写入 `.tmp/dict-decision.json`（不提交），形状见下。
9. 需要改表时使用 `codegen_alter_table(tableId, sql)`；只允许 `ADD`、`MODIFY`、`CHANGE` 和单独的表 `RENAME TO`，禁止 `DROP` 子句和多语句。表重命名只更新物理表名和 `codegen.tableName`，不改类名、业务名、菜单和路由。
10. `codegen_bundle(tableId, basePackage)` 获取 ZIP。
11. 本地运行：

```bash
python3 ~/.agents/skills/f-base-codegen-mcp/scripts/apply_bundle.py \
  --zip .tmp/codegen.zip --ddl .tmp/schema.sql \
  --menu-decision .tmp/menu-decision.json \
  --dict-decision .tmp/dict-decision.json \
  --column-categories .tmp/column-categories.json \
  --dry-run
```

主子表每个表都给一个 `--ddl`（可重复）；脚本会合并全部 DDL。首次应用后会在 `.tmp/f-base-codegen-state.json` 记录源/目标哈希；后处理（`{@link}`、DictFormat、列对齐）完成后的新结果写入 `.tmp/f-base-codegen-base/` 作基线（不提交）。再次落盘时按基线、当前文件、新结果三方合并；同一单位两边都改则跳过该文件并报告，其它文件继续。没有基线时仍更新生成结构，并保留人对齐、已填链接和多出来的方法。确认后可加 `--force` 整文件覆盖并重记基线。

确认目标清单后去掉 `--dry-run` 执行。

第二次生成后观察与后处理（本技能不对这些项做特殊合并；下列须在落盘核对时处理或确认）：

- 字典注解上的待办注释是否仍在或被盖回
- 列宽是否被生成器默认值冲掉
- 菜单名和图标是否仍是结论里的值
- **Dayjs 导入（模板侧暂不改）**：上游 `vue3_vben5_ele/schema/api/api.ts.vm`（antd 经 `#parse` 共用）总会写出 `import type { Dayjs } from 'dayjs';`。落盘后对本次写入的前端 API 文件做技能后处理——若正文里没有任何类型用到 `Dayjs`（无 `| Dayjs` / `: Dayjs`），删除该 import 行；若新增或编辑列含 `date` / `LocalDate` / `LocalDateTime` 等日期类型则保留。不在模板里写死条件，统一在技能侧收尾。

12. 读本地 SQL：父菜单、字典、DDL。
13. 基线 SQL + `sql/mysql/upgrade/` 增量 SQL 双写；无模块 SQL 时新建。增量文件名 `{date}-{moduleName}-{businessName}`，`businessName` 中 `/` 换成 `-`；重名时依次追加 `-2`、`-3`…。`parentMenuId` 不写入 `menu.plan.json`。父菜单先在本地 SQL 中按 path/name 查找；没有则新建一级菜单，同一条父菜单 INSERT 同时写入基线与增量。菜单多条 INSERT 之间不留空行。
14. 补常量/枚举，合并错误码；常量文件已存在就合并，包括空接口；不存在且模块已登记错误码区间就新建。没有数字时首码取 ServiceErrorCodeRange 里该模块的段首。未登记则不写入编号。同名跳过并在标准输出报告名字。手工文件名保持 ErrorCodeConstants_手动操作.java。
15. 只执行增量 SQL；菜单编号按 `sqlRulesPath` 号段取号，需要时用 `--menu-start-id` / `menuStartId` 抬高（不得越过段上界）；本机无 mysql 时使用 `--docker-container mysql8`，密码通过 `docker exec -e MYSQL_PWD=...` 传入；构建 boot/vben 并报告结果。

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

## 字典结论文件

`.tmp/dict-decision.json` 不提交。形状含 `columns[].action`（`bind`|`create`|`none`）与 `creates[]`（仅 create）：

```json
{
  "columns": [
    {"column": "status", "action": "bind", "dictType": "common_status"},
    {"column": "flag", "action": "create", "dictType": "demo_flag"},
    {"column": "token", "action": "none"}
  ],
  "creates": [
    {
      "dictType": "demo_flag",
      "values": [
        {"value": "0", "label": "开启", "constant": "ENABLE"},
        {"value": "1", "label": "关闭", "constant": "DISABLE"}
      ]
    }
  ]
}
```

示例里的 `common_status` / `demo_flag` 只演示 JSON 字段，不是「某列必须绑谁」的规则。只绑定已有字典时 `creates` 为空数组。落盘写字典 INSERT 时，`system_dict_type` 与 `system_dict_data` 的编号各自按模块 SQL 段内最大值加 1，不共用一个最大值。配置 `enums` 对照表把已有字典类型映射到枚举全名（例如 `common_status` → `{basePackage}.framework.common.enums.CommonStatusEnum`）；只写进 Javadoc `{@link}`，不向业务模块 import。

## 枚举格式示例

新建枚举按下面格式写（只说明格式，不写业务列）。取值全是数字时字段类型是 `Integer` 并实现 `ArrayValuable`；取值不全是数字时字段类型为 `String`，不实现 `ArrayValuable`。

```java
@Getter
@AllArgsConstructor
public enum ExampleStatusEnum implements ArrayValuable<Integer> {

    ENABLE(0, "开启"),
    DISABLE(1, "关闭");

    public static final Integer[] ARRAYS = Arrays.stream(values())
            .map(ExampleStatusEnum::getValue).toArray(Integer[]::new);

    private final Integer value;
    private final String name;

    @Override
    public Integer[] array() {
        return ARRAYS;
    }
}
```

## 字段判断停止

出现下面任一情况，不调用 `codegen_update`：

- 十二份缺列，或出现「其余不要」
- 同一列字典结论又绑定又新建
- 常量名不是大写标识符，或同一字典内重复
- 绑定的类型不在本地已有字典里
- 绑定的类型在配置 `enums` 对照表里没有类名
- `select` 或 `radio` 但该列没有 `dictType`
- 新字典类型不以模块名加下划线开头（`{moduleName}_`）
- prompt 写了关联表，正文没有那张表的 CREATE TABLE
- 用户没有点名，三字段却偏离 SQL README 的切段结果
- 用户没有说树表或主子表，`templateType` 却不是 `1`
- prompts.md 没有「列宽定稿」，或定稿表有空单元格、空类别或非整数
- 更新工具无法显式提交空的 `colWidth`
- 菜单名不是 2–6 个汉字，或本页名带「管理」
- 图标不在 prompts.md 的 `ep:` 清单里
- 排序漏列、重复，或不是从 1 开始的连续整数
- 列表要展示的列在列宽步没有类别
- 同一 ZIP 重跑落盘时缺少 `--menu-decision` 或 `--column-categories`（缺 categories 会用 ZIP 覆写掉已写入的 `headerAlign` / `align`）

## 常见失败

| 借口 | 对策 |
|---|---|
| 有外键就该生成主子表 | 用户没说主子表或树表时 `templateType=1` |
| 关联表可以猜 | 找不到就写「无关联表」，不编造 DDL |
| 注释应保持 DDL 原文 | `columnComment` 最多 8 个汉字，去掉括号枚举、预留、加密、不 DROP、存储说明 |
| 列宽让模板默认 120 | 列表列写整数 `colWidth`；不展示的列传 `null`；定稿没有整数就停止 |
| 十二步可以合成一次 | 十二份按列写全之前不调用 `codegen_update` |
| 其余字段沿用导入值 | 出现「其余不要」就重做该步 |
| 页面菜单写成「类注释 + 管理」 | 本页名由菜单 prompt 决定，不带「管理」 |
| 重跑 ZIP 可省略两类 JSON | 每次 `apply_bundle` 都带 `--menu-decision` 与 `--column-categories` |
| `discount_note` comment says ignore / keep column → all ops off (no DROP). | 贴上基线失败原句：列注释不得保留「不 DROP」；须先写短注释再决定开关 |

## 参考

- [reference.md](reference.md)：配置字段、14 工具参数、路径/SQL/枚举规则。
- [GAPS.md](GAPS.md)：已知缺口。记录本身不改变本技能的执行步骤。
- `scripts/project_config.py`：配置读取。
- `scripts/apply_bundle.py`：落盘、SQL、枚举、错误码。
- `tests/`：脚本测试。
