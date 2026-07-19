# Skills 分类目录

本目录是仓库的 **只读派生产物**：内容由 `.agents/skills`（经 `skills-lock.json` 更新）按 `skills-catalog.json` **全量清空后重建**。

## 约定

- **真相源**：`.agents/skills/` + `skills-lock.json`
- **派生产物**：本目录 `skills/`（禁止手改）
- **多分类**：同一 skill 可出现在多个分类下（完整副本）
- **同步方式**：使用 `.cursor/skills/sync-skills-catalog/` 运维 skill（该 skill 不会同步到本目录）
- **第一期**：不提供按框架的 presets 预设包；请按分类手工拷贝所需 skill

## 如何给新项目拷贝

1. 打开对应分类目录（或本页下方链接）
2. 将需要的 skill 文件夹复制到目标项目的 `.agents/skills/`（或该项目约定的 skills 目录）
3. 如目标项目使用 `skills-lock.json`，请按需补齐 lock 条目

## 分类索引

| 分类 | 说明 | Skill 数量 | 入口 |
| --- | --- | ---: | --- |
| `web/react` | Web / React — React、Next.js 与 Ant Design 相关 skills | 7 | [README](web/react/README.md) |
| `web/vue` | Web / Vue — Vue、Nuxt 与 Vben Admin 相关 skills | 2 | [README](web/vue/README.md) |
| `web/design` | Web / 设计 — 前端视觉设计与 Web 界面规范审查 | 2 | [README](web/design/README.md) |
| `java` | Java — Spring Boot、Fan 后端与 Java 重构 | 3 | [README](java/README.md) |
| `spec` | 规范 / Spec — OpenSpec 与规格文档相关 skills | 7 | [README](spec/README.md) |
| `docs` | 文档与办公 — Word、PDF、PPT、表格处理 | 4 | [README](docs/README.md) |
| `workflow` | 工作流 — 规划质询、领域建模、架构词汇与技能发现 | 6 | [README](workflow/README.md) |
| `mcp` | MCP — MCP Server 构建与评估 | 1 | [README](mcp/README.md) |
| `testing` | 测试 — Web 应用自动化测试 | 1 | [README](testing/README.md) |

## 维护

```bash
# 1) 按 lock 更新 .agents/skills（可选）
npx skills update -y

# 2) 全量重建 skills/ 与中文 README
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py
```
