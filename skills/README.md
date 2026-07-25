# Skills 分类目录

本目录是仓库的 **只读派生产物**：内容由 `.agents/skills`（经 `skills-lock.json` 更新）按 `skills-catalog.json` **全量清空后重建**；中文简介与详细说明由 AI 生成。

## 约定

- **真相源**：`.agents/skills/` + `skills-lock.json`
- **分类元数据**：`skills-catalog.json`（不含中文文案）
- **AI 说明缓存**：`.cursor/skills/sync-skills-catalog/generated/skill-docs.json`
- **派生产物**：本目录 `skills/`（禁止手改）
- **同步方式**：使用 `.cursor/skills/sync-skills-catalog/` 运维 skill
- **第一期**：不提供 presets 预设包

## 如何给新项目拷贝

1. 打开对应分类目录，阅读总览表与详细介绍
2. 将需要的 skill 文件夹复制到目标项目的 `.agents/skills/`
3. 如目标项目使用 `skills-lock.json`，请按需补齐 lock 条目

## 分类索引

| 分类 | 说明 | Skill 数量 | 入口 |
| --- | --- | ---: | --- |
| `web/react` | Web / React — React、Next.js 与 Ant Design 相关 skills | 8 | [README](web/react/README.md) |
| `web/vue` | Web / Vue — Vue、Nuxt 与 Vben Admin 相关 skills | 2 | [README](web/vue/README.md) |
| `web/design` | Web / 设计 — 前端视觉设计与 Web 界面规范审查 | 3 | [README](web/design/README.md) |
| `java` | Java — Spring Boot、Fan 后端与 Java 重构 | 3 | [README](java/README.md) |
| `spec` | 规范 / Spec — OpenSpec 与规格文档相关 skills | 7 | [README](spec/README.md) |
| `docs` | 文档与办公 — Word、PDF、PPT、表格处理 | 4 | [README](docs/README.md) |
| `workflow` | 工作流 — 规划质询、领域建模、架构词汇与技能发现 | 11 | [README](workflow/README.md) |
| `mcp` | MCP — MCP Server 构建与评估 | 1 | [README](mcp/README.md) |
| `testing` | 测试 — Web 应用自动化测试 | 2 | [README](testing/README.md) |
| `fan` | Fan 自研 — Fan 团队自行编写、非来自公开开源项目的 skills | 4 | [README](fan/README.md) |

## 维护

```bash
npx skills update -y   # 可选
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status
# 按运维 skill：为 NEED_GENERATE 列表生成/更新 skill-docs.json
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render
```
