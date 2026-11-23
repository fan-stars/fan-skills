# MCP

MCP Server 构建与评估

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-base-codegen-mcp` | `skills/mcp/f-base-codegen-mcp/` | 经远程 Streamable HTTP MCP 把库表生成并落盘到 Fan boot/vben 基础 CRUD，并按八份结论定稿字段、菜单与排序。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-base-codegen-mcp/SKILL.md) |
| `mcp-builder` | `skills/mcp/mcp-builder/` | 设计并实现高质量 MCP Server，让模型通过优质工具调用外部服务。 | [skills.sh](https://skills.sh/anthropics/skills/mcp-builder) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md) |

## 详细介绍

### `f-base-codegen-mcp`

**路径**：`skills/mcp/f-base-codegen-mcp/`

#### 核心能力

按 prompts.md 先写注释、查询、列表、新增、编辑、列宽、菜单、排序八份结论，每份按详情列顺序一列一行（菜单除外），写全后才调用一次 codegen_update；落盘时带 --menu-decision 与 --column-categories，改写中文菜单名并按列宽类别写入 headerAlign/align；标准状态列绑定 common_status；templateType 默认单表；三字段按 SQL README 切段核对；再串行调用 codegen_import/detail/alter/bundle，本地 apply_bundle 幂等落盘并双写菜单、字典、DDL，合并错误码与枚举。

#### 适用场景

需要把数据库表生成 Fan 后端与 Vben 前端基础 CRUD，或在导入后定稿列注释、查询、列表、表单、列宽、菜单名与字段排序，或对已导入表做主子关系、字段与字典调优后重新出包落盘时使用。

#### 主要覆盖内容

八份结论与 prompts.md 列宽/菜单/排序定稿、单表与树表/主子表判定、三字段切段核对、菜单 path+name 查找、列对齐与重跑两类 JSON、字段判断停止条件与常见失败对策、MCP 连通与配置校验、表导入与 detail、codegen_update/alter/bundle、本地 ZIP/DDL 应用、基线与增量 SQL、菜单号段、错误码合并与构建报告。

#### 注意事项

仅用 Streamable HTTP `/mcp`，禁用旧 fan-mcp 工具名与本地/SSE。用户没有点名时，三字段不得偏离 SQL README；没有明确说树表或主子表时一律 templateType=1；出现「其余不要」、漏列或列宽定稿缺整数即停止，不调用 codegen_update；不展示的列传 null，工具丢弃 null 时停止；同一 ZIP 重跑必须带 --menu-decision 与 --column-categories。不覆盖人工改动；写工具串行；不删表不写密钥。

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
