# 测试

Web 应用自动化测试

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `agent-browser` | `skills/testing/agent-browser/` | Rust 浏览器自动化 CLI，用无障碍树快照与 @eN 引用让 Agent 低 token 操作网页。 | [skills.sh](https://skills.sh/vercel-labs/agent-browser/agent-browser) | [GitHub](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/testing/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的项目强隔离、增量证据索引、可恢复运行与失败关闭质量门禁技能。 | 暂无 | [本仓库](../../.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
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

### `f-enterprise-source-reverse-engineering`

**路径**：`skills/testing/f-enterprise-source-reverse-engineering/`

#### 核心能力

按 Project 绑定不同源码根并构建源码、符号和业务三层持久索引；通过完整限定参数类型、调用可达性与已知表关联生成结构事实，把 Service、Repository、Model、Request 等名称信号限制为候选；支持带审核人和时间戳的负向证据安全写入、可信快照、失败阶段续跑、补证后独立终结，以及文件归属、方法调用者和业务规则关联接口与表查询。

#### 适用场景

适用于初始化或刷新两套大型 PHP 项目工作区、逐模块增量逆向、从失败阶段继续分析、为 PARTIAL 运行补齐人工证据后安全终结、查询文件归属或方法调用者、追踪规则关联接口与表、传播并复核过期证据、审计模块完成度，或依据已批准的双项目事实设计可追溯 Java 目标系统。

#### 主要覆盖内容

覆盖 A/B 根目录和事实读取隔离、源码与解析结果增量缓存、解析器版本失效、多模块追加归属及显式角色替换、路由到 Controller、验证、Service、持久化、事务和副作用的接口证据链、PRESENT 与 UNRESOLVED 及经审核的 NOT_APPLICABLE、真实哈希行号、STALE 传播、门禁候选与最终提交分离、完整自动管线及门禁尝试记录、JSON Schema 和十八项门禁。

#### 注意事项

核心脚本仅依赖 Python 标准库并兼容 Windows 与 Linux，Schema 和平台格式测试需安装测试依赖。独立门禁只产生候选结果，补证后必须使用同一运行 ID 的 --finalize 完成最终提交；继续运行会复核实际源码集合与哈希，发现变化时必须创建新运行。可信快照只供刚完成刷新且 token 匹配的单项目管线使用。PHP 解析仍是保守候选解析，动态调用、复杂语法、非 HTTP 入口及是否真正不适用仍需人工补证。

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
