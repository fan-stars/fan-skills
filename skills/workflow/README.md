# 工作流

规划质询、领域建模、架构词汇与技能发现

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `codebase-design` | `skills/workflow/codebase-design/` | 用「深模块」词汇设计小接口、大行为、可测试的代码接缝与边界。 | [skills.sh](https://skills.sh/mattpocock/skills/codebase-design) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) |
| `domain-modeling` | `skills/workflow/domain-modeling/` | 主动打磨项目领域模型：统一语言、边界场景与架构决策落盘。 | [skills.sh](https://skills.sh/mattpocock/skills/domain-modeling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md) |
| `f-base-project-initializer` | `skills/workflow/f-base-project-initializer/` | 从固定 fan-base / fan-base-vben 模板克隆并重命名，生成可运行的 Fan 全栈新项目。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-base-project-initializer/SKILL.md) |
| `f-base-project-initializer-cn` | `skills/workflow/f-base-project-initializer-cn/` | 中文指引：从固定 fan-base / fan-base-vben 模板初始化并重命名 Fan 全栈项目。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-base-project-initializer-cn/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/workflow/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的项目强隔离、增量证据索引、可恢复运行与失败关闭质量门禁技能。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
| `f-project-runtime-manager` | `skills/workflow/f-project-runtime-manager/` | 按探测结果为 Java/Spring Boot 与 React/Next/Vue/Nuxt 等 Node 应用生成可移植启停脚本。 | 暂无 | [GitHub](https://github.com/fan-stars/fan-skills/blob/master/.agents/skills/f-project-runtime-manager/SKILL.md) |
| `find-skills` | `skills/workflow/find-skills/` | 从开放 skills 生态检索并安装可扩展 Agent 能力的技能包。 | [skills.sh](https://skills.sh/vercel-labs/skills/find-skills) | [GitHub](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) |
| `grill-me` | `skills/workflow/grill-me/` | 启动一轮严厉质询会话，压力测试计划或设计直至达成共识。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-me) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) |
| `grill-with-docs` | `skills/workflow/grill-with-docs/` | 严厉质询方案的同时，用领域建模把 ADR 与词汇表边问边写下来。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-with-docs) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) |
| `grilling` | `skills/workflow/grilling/` | 一次只问一个问题，沿决策树严厉追问计划，直到达成共享理解。 | [skills.sh](https://skills.sh/mattpocock/skills/grilling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) |
| `improve-codebase-architecture` | `skills/workflow/improve-codebase-architecture/` | 扫描代码库找加深模块的机会，输出 HTML 报告并质询选定重构方向。 | [skills.sh](https://skills.sh/mattpocock/skills/improve-codebase-architecture) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) |
| `rea-analysis-optimization` | `skills/workflow/rea-analysis-optimization/` | 在保持正确性与 Evidence 的前提下，优化 REA 分析路径的上下文、延迟与资源占用。 | [skills.sh](https://skills.sh/morluto/rea/rea-analysis-optimization) | [GitHub](https://github.com/morluto/rea/blob/main/.agents/skills/rea-analysis-optimization/SKILL.md) |
| `rea-tool-design` | `skills/workflow/rea-tool-design/` | 审计与设计 REA 调查工具、CLI/MCP 契约、provider 能力与 Evidence 语义。 | [skills.sh](https://skills.sh/morluto/rea/rea-tool-design) | [GitHub](https://github.com/morluto/rea/blob/main/.agents/skills/rea-tool-design/SKILL.md) |
| `request-refactor-plan` | `skills/workflow/request-refactor-plan/` | 通过访谈产出小步可验证的重构计划，并可整理为 GitHub Issue。 | [skills.sh](https://skills.sh/mattpocock/skills/request-refactor-plan) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/deprecated/request-refactor-plan/SKILL.md) |
| `reverse-engineer-anything` | `skills/workflow/reverse-engineer-anything/` | 用 REA 对已发布产物做逆向与证据采集，或从线上实例构建 AgentEnv 环境包。 | [skills.sh](https://skills.sh/morluto/rea/reverse-engineer-anything) | [GitHub](https://github.com/morluto/rea/blob/main/.agents/skills/reverse-engineer-anything/SKILL.md) |

## 详细介绍

### `codebase-design`

**路径**：`skills/workflow/codebase-design/`

#### 核心能力

提供 Module/Interface/Implementation/Depth/Seam/Adapter 等统一术语，指导把大量行为藏在小接口后、选对接缝、提升可测性与 AI 可导航性。帮助识别浅模块与加深机会，而非只改命名。

#### 适用场景

设计或重构模块接口、决定边界落点、提升可测试性、让代码更易被 AI 理解，或其他 skill 需要统一「深模块」语言时启用。

#### 主要覆盖内容

术语表、深度与浅度判断、接缝选择、适配器与实现区分、面向调用方杠杆与维护局部性的设计原则。刻意避免用 component/service/API 等含糊替代词。

#### 注意事项

这是共享设计词汇，不是具体框架教程。讨论时必须沿用文中术语，避免自创近义词导致沟通漂移。

### `domain-modeling`

**路径**：`skills/workflow/domain-modeling/`

#### 核心能力

在设计过程中质询术语、发明边界场景，并把词汇表与 ADR 写到 CONTEXT.md / docs/adr；支持单上下文或多上下文（CONTEXT-MAP）仓库。

#### 适用场景

要钉死领域用语、记录架构决策，或其他 skill 需要同步维护领域模型时使用。仅阅读词汇表不算本 skill，改模型才算。

#### 主要覆盖内容

文件布局、会话中挑战模糊语言、及时落盘 glossary 与 ADR、多限界上下文映射。

#### 注意事项

文件应惰性创建：有内容再写。术语冲突要立刻对齐；决策写 ADR，日常用语写 CONTEXT.md。

### `f-base-project-initializer`

**路径**：`skills/workflow/f-base-project-initializer/`

#### 核心能力

从固定 Gitee 模板克隆后端与 Vben 前端，重命名目录与标识，迁移配置，再调用 `$f-project-runtime-manager` 在 `scripts/runtime/<os>/` 生成启停脚本，并可用 `$create-agentsmd` 写根目录 AGENTS.md。

#### 适用场景

用户要从 fan-base / fan-base-vben 快速搭一套可运行 Fan 全栈新项目，并顺带生成根目录启停脚本与 AGENTS.md 时使用。

#### 主要覆盖内容

模板克隆与重命名、Maven/包标识迁移、数据库与配置安全边界、`scripts/runtime/<os>/` 运行脚本与外置 config、根 AGENTS.md、启动校验与交付检查。

#### 注意事项

目标目录非空禁止覆盖。未提供目标远程时不得推送。运行覆盖只写 `scripts/runtime/<os>/config/`，不改项目既有配置文件。英文版与中文版流程一致，按对话语言选用。

### `f-base-project-initializer-cn`

**路径**：`skills/workflow/f-base-project-initializer-cn/`

#### 核心能力

以中文步骤从固定 Gitee 模板克隆并重命名 Fan 全栈项目，迁移配置后调用 `$f-project-runtime-manager` 生成 `scripts/runtime/<os>/` 启停脚本，并可生成根目录 AGENTS.md。

#### 适用场景

中文对话中要从 fan-base / fan-base-vben 初始化 Fan 全栈项目，并需要统一运行脚本与根目录说明文档时使用。

#### 主要覆盖内容

中文流程说明、模板克隆与重命名、配置迁移、runtime 脚本与外置 config、根 AGENTS.md、启动验证与交付检查；与英文版同源。

#### 注意事项

与英文版 `f-base-project-initializer` 同源，按用户语言二选一，勿同时执行。非空目标目录不得覆盖；无用户远程时不推送。运行参数只写 `scripts/runtime/<os>/config/`。

### `f-enterprise-source-reverse-engineering`

**路径**：`skills/workflow/f-enterprise-source-reverse-engineering/`

#### 核心能力

按 Project 绑定不同源码根并构建源码、符号和业务三层持久索引；通过完整限定参数类型、调用可达性与已知表关联生成结构事实，把 Service、Repository、Model、Request 等名称信号限制为候选；支持工作区内的外部权威 SQL 快照、带审核人和时间戳的负向证据安全写入、可信快照、失败阶段续跑、补证后独立终结，以及文件归属、方法调用者和业务规则关联接口与表查询。

#### 适用场景

适用于初始化或刷新两套大型 PHP 项目工作区、引用源码根外的权威数据库 dump、逐模块增量逆向、从失败阶段继续分析、为 PARTIAL 运行补齐人工证据后安全终结、查询文件归属或方法调用者、追踪规则关联接口与表、传播并复核过期证据、审计模块完成度，或依据已批准的双项目事实设计可追溯 Java 目标系统。

#### 主要覆盖内容

覆盖 A/B 根目录和事实读取隔离、源码与解析结果增量缓存、外部 SQL 的工作区边界及真实文件哈希行号校验、解析器版本失效、多模块追加归属及显式角色替换、路由到 Controller、验证、Service、持久化、事务和副作用的接口证据链、PRESENT 与 UNRESOLVED 及经审核的 NOT_APPLICABLE、STALE 传播、门禁候选与最终提交分离、完整自动管线及门禁尝试记录、JSON Schema 和十八项门禁。

#### 注意事项

核心脚本仅依赖 Python 标准库并兼容 Windows 与 Linux，Schema 和平台格式测试需安装测试依赖。外部 SQL 必须位于分析工作区内，不能用范围标记绕过文件存在、SHA-256、扩展名和行号检查；源码可信快照也不豁免这些检查。独立门禁只产生候选结果，补证后必须使用同一运行 ID 的 --finalize 完成最终提交。PHP 解析仍是保守候选解析，动态调用、复杂语法、非 HTTP 入口及是否真正不适用仍需人工补证。

### `f-project-runtime-manager`

**路径**：`skills/workflow/f-project-runtime-manager/`

#### 核心能力

先探测工作区候选运行根与唯一主入口，再在 scripts/runtime/<os>/ 生成 start/stop/restart/status（多入口另有 *-all）；外置 config/*.env.example；按 PID、命令行与工作目录核对后停进程。进程库含 macos、linux 的 bash 与 windows 的 PowerShell 5.1，默认只生成当前系统。

#### 适用场景

用户要求项目启动脚本、本地前后端进程管理，或提到 spring.application.name、scripts/runtime、macos、linux、windows 时使用，覆盖单模块与多模块仓库。

#### 主要覆盖内容

候选根判定、Java 与 Node 主入口及脚本基名、run 与 jar 命令、PID 停止算法、gitignore 规则、再次生成时的差异确认。细节见 reference.md、examples.md，以及 templates 下 macos、linux、windows 三份进程库。

#### 注意事项

不改项目既有配置与源文件；主入口不明确时只列候选并等待。禁止 killall、pkill、taskkill /IM java 和按进程名模糊匹配。已有脚本不一致时先展示 diff，真实 .env 永不覆盖。三份进程库必须原样复制。Fan 本地自建 skill。

### `find-skills`

**路径**：`skills/workflow/find-skills/`

#### 核心能力

在用户想找「会不会有现成 skill」时，用 `npx skills find/add/update` 与 skills.sh 排行榜发现、安装与更新技能，把需求映射到领域与任务再搜索。

#### 适用场景

用户问「怎么做 X」「有没有 skill」「能否扩展能力」，或希望为设计/测试/部署等领域寻找现成包时使用。

#### 主要覆盖内容

Skills CLI 关键命令、先看排行榜再 CLI 搜索、安装来源与更新流程、帮助用户判断任务是否足够常见。

#### 注意事项

先理解领域与任务再搜，避免盲目安装。安装后仍需按目标项目约定放入正确 skills 目录并必要时更新 lock。

### `grill-me`

**路径**：`skills/workflow/grill-me/`

#### 核心能力

作为入口触发 `/grilling` 流程：逐个决策追问、给出推荐答案、走完决策树依赖，直到双方共享理解后再行动。

#### 适用场景

用户明确要求 grill/质询、或要对方案做压力测试且只需会话、不强制同步写文档时使用。

#### 主要覆盖内容

仅作为启动 grilling 会话的薄封装入口；具体追问规则、单问单答与共识门槛见 grilling skill 正文。

#### 注意事项

实质规则在 `grilling`。需要边问边写 ADR/词汇表时改用 `grill-with-docs`。

### `grill-with-docs`

**路径**：`skills/workflow/grill-with-docs/`

#### 核心能力

组合 `/grilling` 与 `/domain-modeling`：一边拆决策树，一边把固化术语与架构决策写入 CONTEXT.md 与 ADR。

#### 适用场景

既要压力测试计划或设计，又希望会话结束留下可复用领域词汇表与架构决策记录（ADR）时使用。

#### 主要覆盖内容

质询节奏与领域建模落盘纪律的联合工作流；术语写入 CONTEXT.md，决策写入 docs/adr，细节仍分别遵循两个基础 skill。

#### 注意事项

必须同时遵循 grilling 与 domain-modeling。事实可查环境，决策须等人确认；未达成共识前不要开写实现。

### `grilling`

**路径**：`skills/workflow/grilling/`

#### 核心能力

对计划、决策或想法做无情面试：逐分支澄清依赖、每题给推荐答案、等人回复再继续；可查的事实自己查，决策留给用户。

#### 适用场景

用户要 stress-test 想法，或使用 grill 类触发语；在动手实现前需要把模糊方案问清楚时启用。

#### 主要覆盖内容

单问单答节奏、决策树遍历、推荐答案、环境探查与决策提问的分工、确认共识前不得擅自执行。

#### 注意事项

禁止一次抛多个问题以免干扰决策。未确认双方已达成共享理解之前，不要开始改代码或落地实现。

### `improve-codebase-architecture`

**路径**：`skills/workflow/improve-codebase-architecture/`

#### 核心能力

探索热点与浅模块，用深模块词汇提出加深机会，生成可视化 HTML 报告，再对用户选定的一项做 grilling，目标是提升可测性与 AI 可导航性；依赖 codebase-design 术语与可选 CONTEXT.md/ADR。

#### 适用场景

迁移或大规模重构前需要划清模块边界、找出耦合与难测接缝，或想把原生页面逻辑重组为更深接口时使用；适合 H5 改 React 时先梳理架构摩擦。

#### 主要覆盖内容

基于提交热点的范围选择、Explore 摩擦点、删除测试、HTML 报告产出与打开、选定机会后的质询流程，以及与 domain glossary/ADR 的衔接。

#### 注意事项

标记 disable-model-invocation，需显式触发。报告写在系统临时目录，不入库。上游已与 codebase-design 配套；本库 path 为 engineering 下正式 skill。

### `rea-analysis-optimization`

**路径**：`skills/workflow/rea-analysis-optimization/`

#### 核心能力

先钉住分析问题与独立正确性预言，再定位最早多余工作，按复用、投影下推、增量解码等策略改所有者实现，并用等价完整调查验证；也可给出有据的「不改」决定。

#### 适用场景

分析链路过慢、上下文膨胀、CPU/内存过高、缓存或查询设计存疑，且目标是分析路径而非整套 CI/测试套件优化时使用。

#### 主要覆盖内容

涵盖基线记录、预言构建、成本表与候选修正、Kuna 等案例参考、测量与正确性并重的验证方式，以及日常清理不必强行走本优化流程的边界。

#### 注意事项

性能测试只服务于明确性能目标或回归疑虑。禁止为「看起来更干净」引入无收益的缓存或编排层。CI/测试套件优化应改用专门审计技能。

### `rea-tool-design`

**路径**：`skills/workflow/rea-tool-design/`

#### 核心能力

按工具设计指南界定边界、输入输出与可发现性，对照现有最近似工具与实机工作流，区分复现缺陷、已知限制与设计机会，并给出验证与恢复策略。

#### 适用场景

新增或改造 REA 工具、评审 MCP/CLI 契约、澄清 Evidence 字段含义、做工具审计或需要在实现前写清边界与验证方式时使用。

#### 主要覆盖内容

覆盖审计流程、设计提案要素（边界、形状、Evidence、替代方案、验证）、provider 工作流核验，以及失败恢复与文档权威版本差异提醒。

#### 注意事项

以当前契约与实机能力为准，文档可能滞后。不要为追求 API 对等而忽视任务证据；实现与验证仍须遵守测试与贡献约定。

### `request-refactor-plan`

**路径**：`skills/workflow/request-refactor-plan/`

#### 核心能力

引导用户描述问题与方案，探查仓库现状与测试覆盖，界定范围内外，把改造拆成尽量小的可工作提交清单，并按模板整理问题陈述、方案、决策与测试约定。

#### 适用场景

要把原生 HTML/JS 迁到 React+Ant Design+Next，或任何大型重构需要先立 RFC/Issue、避免一步改崩时使用。

#### 主要覆盖内容

访谈步骤、选项对比、范围敲定、测试策略、tiny commits 计划模板（Problem/Solution/Commits/Decision/Testing/Out of Scope）。

#### 注意事项

上游路径在 deprecated 目录，仍可用但需知可能不再积极演进。创建 GitHub Issue 需仓库权限；也可只输出计划文本。与 grilling/openspec 可组合使用。

### `reverse-engineer-anything`

**路径**：`skills/workflow/reverse-engineer-anything/`

#### 核心能力

指导在依赖二进制、反编译、运行时观测或版本对比时接入 REA，按目标路由到原生/托管/Electron/固件/浏览器等工具链，并维护完整 Evidence；也可从抓包或实机导出 AgentEnv。

#### 适用场景

分析已发布包行为、比较版本差异、反编译关键逻辑、构建可复现的调查环境，或普通源码仓库工具无法支撑结论时启用；完整源码架构梳理则不必用 REA。

#### 主要覆盖内容

涵盖连接与恢复、目标分流、摘要优先工作流、多类制品指南入口，以及不把 skill 安装等同于 MCP/引擎已就绪的边界说明。

#### 注意事项

安装本技能不会自动注册 MCP 或引擎；插件安装例外。超时、权限与注册失败要按恢复指南处理，勿盲目重复 setup。结论须区分观测、推断与未知。
