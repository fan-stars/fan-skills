# 测试

Web 应用自动化测试

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `agent-browser` | `skills/testing/agent-browser/` | Rust 浏览器自动化 CLI，用无障碍树快照与 @eN 引用让 Agent 低 token 操作网页。 | [skills.sh](https://skills.sh/vercel-labs/agent-browser/agent-browser) | [GitHub](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/testing/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的根目录强隔离、增量证据索引与失败关闭式质量门禁技能。 | 暂无 | [本仓库](../../.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
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

按 Project 绑定不同且不可静默切换的源码根，构建源码、符号和业务三层持久索引，按哈希增量复用符号、路由与表解析结果；支持文件归属、方法调用者、规则关联接口和表查询，并以真实哈希行号、调用可达性、类型化业务字段、完整运行记录及两阶段状态提交阻止不完整分析冒充完成。

#### 适用场景

适用于初始化或刷新两套 PHP 项目工作区、逐模块增量逆向、查询文件模块归属或方法调用者、追踪业务规则关联接口与表、传播和复核过期证据、严格审计模块完成度，或依据已批准的双项目事实设计可追溯 Java 目标系统。

#### 主要覆盖内容

覆盖 A/B 项目标识与单一根目录绑定、读取前路径隔离、源码和解析结果增量缓存、多模块追加归属、路由到事务及副作用的接口证据链、业务语义条件字段、真实哈希行号、项目内 STALE 传播、可恢复排他锁、JSON Schema、完整运行轨迹和十八项门禁。

#### 注意事项

核心脚本使用 Python 标准库处理 Windows 与 Linux 路径、进程和锁恢复；Schema 与平台格式测试需安装测试依赖。默认源码增量依赖大小和修改时间，时间戳可能被保留时应使用 --verify-all。PHP 解析保持保守候选精度，动态调用、复杂语法及非 HTTP 模块仍需人工补证，缺少状态、并发或跨模块事实时只能保持部分完成。

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
