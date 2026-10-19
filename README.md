# fan-skills

Fan 项目选用的 Agent Skills **目录库**：供其他新项目按技术栈挑选并拷贝所需 skills。

## 目录说明

| 路径 | 角色 |
| --- | --- |
| `.agents/skills/` | **真相源**（经 `skills-lock.json` 安装/更新） |
| `skills/` | **只读派生产物**（按分类多副本，禁止手改） |
| `commands/` | opsx / superpowers 配套 slash 命令（canonical 嵌套；可占位） |
| `skills-catalog.json` | 分类映射与中文简介 |
| `.cursor/skills/sync-skills-catalog/` | 运维同步 skill（**不**进入分类目录） |

## 远程与推送

| 远程名 | 地址 | 用途 |
| --- | --- | --- |
| `origin` | `git@gitee.com:fan-stars/fan-skills.git` | **日常 push / pull** |
| `github` | `git@github.com:fan-stars/fan-skills.git` | 对照 / fetch；**不要 push** |

Gitee 已配置自动同步到 GitHub：推送到 `origin` 即可，无需再推 `github`。

## 更新与同步

```bash
# 可选：按 lock 更新上游 skill
npx skills update -y

# 全量重建 skills/ 与中文 README
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py
```

或在 Cursor 中触发 skill：`sync-skills-catalog`。

## 给新项目拷贝

1. 打开 [`skills/README.md`](skills/README.md) 浏览分类  
2. 将需要的 skill 目录复制到目标项目的 `.agents/skills/`  
3. 第一期**不提供** presets 预设包  

## 分类一览

- `skills/web/react` — React / Ant Design / Next  
- `skills/web/vue` — Nuxt / Vben  
- `skills/web/design` — 视觉与界面规范（含 Finesse / Frame-smith）  
- `skills/java` — Spring Boot / Fan 后端 / GraalVM  
- `skills/openspec-legacy` — 旧版 OpenSpec 套件  
- `skills/opsx/openspec` — 新 OpenSpec（`/opsx:*`）  
- `skills/opsx/superpowers` — Superpowers（`/superpowers:*`）  
- `commands/opsx` · `commands/superpowers` — 配套 slash 命令（canonical；可占位）  
- `skills/spec` — 通用规格（create-agentsmd 等，不含 OpenSpec 套件）  
- `skills/docs` — 办公文档  
- `skills/workflow` — 质询与建模  
- `skills/mcp` — MCP 构建  
- `skills/testing` — Web 测试  
- `skills/fan` — Fan 自研技能  

