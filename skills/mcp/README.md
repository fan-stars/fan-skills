# MCP

MCP Server 构建与评估

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-base-codegen-mcp` | `skills/mcp/f-base-codegen-mcp/` | 经远程 Streamable HTTP MCP 把库表生成并落盘到 Fan boot/vben 基础 CRUD，定稿字段、字典与菜单后写模块号段。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-base-codegen-mcp/SKILL.md) |
| `mcp-builder` | `skills/mcp/mcp-builder/` | 设计并实现高质量 MCP Server，让模型通过优质工具调用外部服务。 | [skills.sh](https://skills.sh/anthropics/skills/mcp-builder) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md) |

## 详细介绍

### `f-base-codegen-mcp`

**路径**：`skills/mcp/f-base-codegen-mcp/`

#### 核心能力

先按 prompts.md 写注释、字典、查询、查询方式、显示类型、允许空、列表、插入、编辑、列宽、菜单、排序十二份结论，把菜单、字典与列宽类别写入 .tmp 结论文件后只调用一次 codegen_update；串行使用 codegen_list/detail/import/update/sync/preview/create_table/bundle 等 14 个工具；本地 apply_bundle 按基线、当前文件、新结果三方合并，写字典与枚举、菜单名与按钮名，并做 {@link}、DictFormat 与列对齐后处理；新模块用 register_module.py 把号段登记进 SQL README 与 ServiceErrorCodeRange。

#### 适用场景

需要把数据库表生成 Fan 后端与 Vben 前端基础 CRUD，或在导入后定稿列注释、字典、查询、列表、表单、列宽与菜单时使用；也用于为新业务模块登记号段与错误码区间，或二次生成后核对字典注解、列宽、菜单名有没有被生成器默认值冲掉。

#### 主要覆盖内容

十二份结论与 prompts.md 列宽定稿、字典 bind/create/none 决策与 .tmp 结论文件、单表与树表/主子表判定、三字段切段核对、register_module 的号段与错误码登记（默认 dry-run、输出 diff）、字段判断停止与常见失败、14 个远程工具、apply_bundle 三方合并与基线状态、字典与枚举 SQL 及 enums 映射、菜单图标与按钮名、错误码合并与构建报告。

#### 注意事项

每列都要给出字典结论：绑定已有字典、新建字典或不绑；不按列名语义猜绑定关系。仅用 Streamable HTTP `/mcp`，禁用旧工具名与本地/SSE。配置 sqlRulesPath 时模块必须已登记，未登记先用 register_module 登记，脚本不绑定分支名；用户没有点名时三字段不得偏离 SQL README；没说树表或主子表时 templateType=1；缺一份、漏一列或出现「其余不要」即停止；不展示的列传 null；.tmp 结论与基线不提交；不删表不写密钥。

### `mcp-builder`

**路径**：`skills/mcp/mcp-builder/`

#### 核心能力

覆盖从调研规划到实现评估的全流程：工具命名与可发现性、工作流工具与 API 覆盖平衡、分页过滤、可操作错误信息，以及 Python FastMCP / Node MCP SDK 实现指引。

#### 适用场景

要把外部 API 或服务暴露给 LLM、新建或重构 MCP Server、评估工具设计是否利于完成真实任务时启用。

#### 主要覆盖内容

四阶段工作流（调研规划、设计、实现、评估）、工具命名与错误信息原则；强调以真实任务完成度而非端点堆砌作为质量标尺。

#### 注意事项

优先清晰前缀与面向动作的命名。返回宜精炼可过滤；错误信息要给出下一步建议，避免无上下文失败。
