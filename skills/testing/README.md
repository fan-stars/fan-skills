# 测试

Web 应用自动化测试

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `agent-browser` | `skills/testing/agent-browser/` | Rust 浏览器自动化 CLI，用无障碍树快照与 @eN 引用让 Agent 低 token 操作网页。 | [skills.sh](https://skills.sh/vercel-labs/agent-browser/agent-browser) | [GitHub](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) |
| `webapp-testing` | `skills/testing/webapp-testing/` | 用 Playwright 与辅助脚本测试本地 Web 应用：交互、截图与日志。 | [skills.sh](https://skills.sh/anthropics/skills/webapp-testing) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) |

## 详细介绍

### `agent-browser`

**路径**：`skills/testing/agent-browser/`

#### 核心能力

通过 CDP 驱动 Chrome/Chromium，无需 Playwright/Puppeteer，用无障碍树快照与紧凑 @eN 引用完成导航、点击、填表、抽取、截图、多标签与并行会话；本 SKILL.md 仅是发现桩，真实用法由 `agent-browser skills get core` 运行时提供，并有 electron/slack/dogfood 等专项子技能。

#### 适用场景

需要操作网站、填表点击、抓取数据、截图、登录、测试 Web 应用或做探索性 QA，以及自动化 Electron 桌面应用、Slack、Vercel Sandbox、AgentCore 云浏览器时使用。

#### 主要覆盖内容

core 工作流与故障排查、@eN 引用模型、专项技能清单（electron/slack/dogfood/vercel-sandbox/agentcore），以及安装与版本自更新约定。

#### 注意事项

使用前先 `npm i -g agent-browser && agent-browser install`，并用 `skills get core` 加载最新指令而非依赖本桩。与仓库已有 `webapp-testing` 在浏览器自动化上有重叠，按场景择一。

### `webapp-testing`

**路径**：`skills/testing/webapp-testing/`

#### 核心能力

编写原生 Python Playwright 脚本验证前端行为；用 with_server 管理服务生命周期；先侦察 DOM/截图再定位选择器执行操作。

#### 适用场景

需要验证本地前端功能、调试交互异常、捕获页面截图，或查看浏览器控制台日志以定位问题时使用。

#### 主要覆盖内容

静态 HTML vs 动态应用决策树、服务器已启动/未启动分支、with_server 用法与脚本优先 `--help` 的约定。

#### 注意事项

先跑脚本 `--help`，勿一上来通读巨大脚本源码。选择器应来自实际渲染结果，避免臆造。
