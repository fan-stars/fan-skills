# Web / React

React、Next.js 与 Ant Design 相关 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `ant-design` | `skills/web/react/ant-design/` | antd 6.x 与 Pro/X 组件选型、主题与 CLI 决策指南，偏官方 API 而非教程。 | [skills.sh](https://skills.sh/ant-design/antd-skill/ant-design) | [GitHub](https://github.com/ant-design/antd-skill/blob/main/skills/ant-design/SKILL.md) |
| `antd` | `skills/web/react/antd/` | 基于 @ant-design/cli 的离线 antd 知识库：查 API、示例、文档、诊断与迁移。 | [skills.sh](https://skills.sh/ant-design/antd-skill/antd) | [GitHub](https://github.com/ant-design/antd-skill/blob/main/skills/antd/SKILL.md) |
| `f-antd-spacing-layout-governance` | `skills/web/react/f-antd-spacing-layout-governance/` | Ant Design 项目间距与跨页布局契约治理。 | 暂无 | [本仓库](../../../.agents/skills/f-antd-spacing-layout-governance/SKILL.md) |
| `frontend-design` | `skills/web/react/frontend-design/` | 做有辨识度的前端视觉设计：排版、调色与布局避免模板感默认解。 | [skills.sh](https://skills.sh/anthropics/skills/frontend-design) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) |
| `next` | `skills/web/react/next/` | 用 @json-render/next 把 JSON 规格渲染成带路由与 SSR 的 Next.js 应用。 | [skills.sh](https://skills.sh/vercel-labs/json-render/next) | [GitHub](https://github.com/vercel-labs/json-render/blob/main/skills/next/SKILL.md) |
| `next-browser` | `skills/web/react/next-browser/` | 把 React DevTools 与 Next.js dev overlay 变成 shell 命令，供 Agent 调试 Next 应用。 | [skills.sh](https://skills.sh/vercel-labs/next-browser/next-browser) | [本仓库](../../../.agents/skills/next-browser/SKILL.md) |
| `vercel-composition-patterns` | `skills/web/react/vercel-composition-patterns/` | 用组合式 React 模式消除布尔 props 膨胀，构建灵活可维护组件 API。 | [skills.sh](https://skills.sh/vercel-labs/agent-skills/vercel-composition-patterns) | [GitHub](https://github.com/vercel-labs/agent-skills/blob/main/skills/composition-patterns/SKILL.md) |
| `vercel-react-best-practices` | `skills/web/react/vercel-react-best-practices/` | Vercel 出品的 React/Next 性能规则集：消除瀑布、瘦包与渲染优化。 | [skills.sh](https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices) | [GitHub](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md) |
| `vercel-react-view-transitions` | `skills/web/react/vercel-react-view-transitions/` | 用 React View Transition API 做原生感页面与元素过渡动画。 | [skills.sh](https://skills.sh/vercel-labs/agent-skills/vercel-react-view-transitions) | [GitHub](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-view-transitions/SKILL.md) |

## 详细介绍

### `ant-design`

**路径**：`skills/web/react/ant-design/`

#### 核心能力

覆盖组件选型、Design Token 主题、SSR、无障碍、性能、路由权限与 CRUD、Ant Design X 对话 UI，以及通过 `@ant-design/cli` 离线查询 API、示例、迁移与用法分析。强调先查官方元数据再写代码，避免凭记忆臆造 API。

#### 适用场景

在 React 18/19 项目中编写或改造 antd 代码、排查组件行为、做主题定制或版本迁移、分析仓库中 antd 用法时启用。也适用于需要 ProComponents 或 Ant Design X 的中后台与 AI 聊天界面。

#### 主要覆盖内容

目标栈为 antd 6、Ant Design Pro 5/ProComponents、Ant Design X v2；包含 ConfigProvider、tokens/`classNames`/`styles`、CLI 的 info/demo/doc/lint/doctor 等工作流，以及迁移与 changelog 查阅。

#### 注意事项

决策向指南，不是终端用户教程；只依据官方文档，勿耦合内部 `.ant-*` 类名。改代码前后应用 CLI 查 API 与 lint；版本需与本地 node_modules 或 `--version` 对齐。

### `antd`

**路径**：`skills/web/react/antd/`

#### 核心能力

在本地用 `antd` CLI 查询组件 props、demo、semantic 样式、design token、完整文档，并支持项目分析、调试与跨版本迁移。全部元数据离线可用，输出统一要求 `--format json` 便于程序解析。

#### 适用场景

写 antd 组件前查 API、需要完整中英文文档、代码行为异常需对照官方能力、做 v4/v5/v6 迁移或批量检查仓库用法时使用。

#### 主要覆盖内容

涵盖 info/demo/semantic/token/doc、调试流程、迁移与项目分析命令；内置 v4/v5/v6 元数据。首次使用需安装 `@ant-design/cli`，发现更新提示时应先升级 CLI。

#### 注意事项

不要凭记忆写 props；始终加 `--format json`。本 skill 侧重 CLI 操作，更广的选型与架构决策可配合 `ant-design` skill。

### `f-antd-spacing-layout-governance`

**路径**：`skills/web/react/f-antd-spacing-layout-governance/`

#### 核心能力

提供审计规则、迁移策略、扫描脚本与容器模板，统一间距语义。并给出可执行的步骤与约束说明。

#### 适用场景

Ant Design 6 项目出现间距混乱、迁移或 PR 审计时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 token 规则、gap/margin、响应式与页面契约。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

先定布局契约再改组件，避免只调像素不改结构。与用户显式指令冲突时以用户指令为准。

### `frontend-design`

**路径**：`skills/web/react/frontend-design/`

#### 核心能力

以设计主导视角做有主见的美学选择：锚定题材与受众、英雄区命题、字体配对、氛围背景与动效层次，刻意规避常见 AI 模板审美。

#### 适用场景

新建页面或重塑现有 UI、需要独特视觉方向而非通用后台皮肤、落地页与品牌向界面设计时启用。

#### 主要覆盖内容

题材锚定、英雄区原则、字体与色彩方向、减少卡片/杂讯、用动效建立层级等设计原则。

#### 注意事项

若已有设计系统，应服从现有语言。先钉死产品题材再开做；不要堆无意义的渐变与徽章。

### `next`

**路径**：`skills/web/react/next/`

#### 核心能力

将 NextAppSpec（metadata、layouts、routes、page elements）转为完整 Next 应用，支持布局槽位、多页面路由、SSR 与元数据，适合 AI 生成多页应用。

#### 适用场景

使用 `@json-render/next`、从 JSON 规格搭建 Next 应用，或需要程序化生成多路由页面时使用。

#### 主要覆盖内容

依赖安装、spec 结构、createNextApp 用法、布局与路由声明、与 core/react 包的配合。

#### 注意事项

需要同时理解 json-render 元素模型与 Next App Router 约定。规格错误会导致路由/布局缺失，改 spec 后应验证页面可构建。

### `next-browser`

**路径**：`skills/web/react/next-browser/`

#### 核心能力

以结构化文本暴露组件树、props、hooks、PPR shell、错误、网络与无障碍快照，让 Agent 无需人工打开 DevTools 即可 `snapshot`→读输出→`click eN` 地迭代调试。命令是对常驻浏览器守护进程的一次性调用。

#### 适用场景

调试 Next.js 应用、检查 React 组件状态、诊断水合错误、优化路由切换或首屏渲染性能时使用；需要项目使用 Next.js 且启动了 dev server。

#### 主要覆盖内容

CLI 安装与版本检查、tree/snapshot/errors/network 等命令模型，以及 Next.js 16.2+ 内置文档（node_modules/next/dist/docs/）优先阅读的约定。

#### 注意事项

需先全局安装 `@vercel/next-browser` 并 `playwright install chromium`。仓库中无 SKILL.md，本 skill 手动依据 skills.sh 内容维护；做 PPR/Cache Components 前应读内置文档而非依赖记忆。

### `vercel-composition-patterns`

**路径**：`skills/web/react/vercel-composition-patterns/`

#### 核心能力

提供 compound components、状态上提、Context 接口与 React 19 相关模式，按优先级组织 architecture/state/patterns 规则，利于人与 AI 共同维护组件库。

#### 适用场景

重构布尔开关过多的组件、设计可复用组件库 API、审查 compound components 或 Context 组合式架构时启用。

#### 主要覆盖内容

避免 boolean props、复合组件、Provider 解耦状态、泛型 context 接口、React 19 API 等规则条目。

#### 注意事项

优先改架构而非继续加 flag。规则按影响优先级应用；与性能向的 `vercel-react-best-practices` 互补而非替代。

### `vercel-react-best-practices`

**路径**：`skills/web/react/vercel-react-best-practices/`

#### 核心能力

按影响优先级提供约 70 条规则，覆盖异步瀑布、包体积、服务端与客户端取数、重渲染、渲染与 JS 性能及高级模式，指导编写与评审。

#### 适用场景

写或重构 React/Next 页面与数据获取、优化包体与加载、做性能向 code review 时使用。

#### 主要覆盖内容

八大类别前缀（async/bundle/server/client/rerender 等）及快速参考条目。

#### 注意事项

按 CRITICAL→LOW 优先改高影响项。规则多，宜针对当前改动子集应用，避免一次机械套用全部。

### `vercel-react-view-transitions`

**路径**：`skills/web/react/vercel-react-view-transitions/`

#### 核心能力

指导用 `<ViewTransition>`、过渡类型与 CSS 伪元素实现共享元素、Suspense 显现、列表身份、进出场与路由级转场；不支持的浏览器优雅降级。

#### 适用场景

要做路由动画、共享元素、列表重排、前进后退方向动画，或在 Next 中集成 view transitions 时启用。

#### 主要覆盖内容

何时动画、共享元素/Suspense/列表/进出场/路由优先级、导航方向类型、CSS 控制方式以及与 startTransition/useDeferredValue 的配合。

#### 注意事项

每个过渡都应表达空间关系或连续性；说不清语义就不要加。按优先级实现适用模式，而非只挑一个花活。
