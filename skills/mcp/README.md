# MCP

MCP Server 构建与评估

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `mcp-builder` | `skills/mcp/mcp-builder/` | 设计并实现高质量 MCP Server，让模型通过优质工具调用外部服务。 | [skills.sh](https://skills.sh/anthropics/skills/mcp-builder) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/SKILL.md) |

## 详细介绍

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
