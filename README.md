# fan-skills

Fan 项目选用的 Agent Skills **目录库**：供其他新项目按技术栈挑选并拷贝所需 skills。

## 目录说明

| 路径 | 角色 |
| --- | --- |
| `.agents/skills/` | **真相源**（经 `skills-lock.json` 安装/更新） |
| `skills/` | **只读派生产物**（按分类多副本，禁止手改） |
| `commands/` | opsx / superpowers 配套 slash 命令（canonical 嵌套；可占位） |
| `skills-catalog.json` | 分类映射（无中文文案） |

本仓只保留内容库（`.agents/skills` 与派生 `skills/`）。运维脚本在父工作区 **`fan-skills-dir`**：

- 分类重建：`fan-skills-dir/.agents/skills/f-skills-catalog/scripts/sync.py`
- 全局安装与卸载：`fan-skills-dir/.agents/skills/f-skills-sync/scripts/sync.py`

## 远程与推送

| 远程名 | 地址 | 用途 |
| --- | --- | --- |
| `origin` | `git@gitee.com:fan-stars/fan-skills.git` | **日常 push / pull** |
| `github` | `git@github.com:fan-stars/fan-skills.git` | 对照 / fetch；**不要 push** |

Gitee 已配置自动同步到 GitHub：推送到 `origin` 即可，无需再推 `github`。

## 更新与同步

在 **`fan-skills-dir`** 根目录：

```bash
# 可选：按 lock 更新上游 skill（在本库根）
npx skills update -y

# 分类目录 status →（补 AI 说明）→ render → validate
python3 .agents/skills/f-skills-catalog/scripts/sync.py status
python3 .agents/skills/f-skills-catalog/scripts/sync.py render
python3 .agents/skills/f-skills-catalog/scripts/sync.py validate

# 全局安装 / 卸载 / 从全局拉回内容库
python3 .agents/skills/f-skills-sync/scripts/sync.py status
python3 .agents/skills/f-skills-sync/scripts/sync.py apply --skill NAME
```

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
