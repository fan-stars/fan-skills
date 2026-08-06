# 工作流

规划质询、领域建模、架构词汇与技能发现

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `codebase-design` | `skills/workflow/codebase-design/` | 用「深模块」词汇设计小接口、大行为、可测试的代码接缝与边界。 | [skills.sh](https://skills.sh/mattpocock/skills/codebase-design) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) |
| `domain-modeling` | `skills/workflow/domain-modeling/` | 主动打磨项目领域模型：统一语言、边界场景与架构决策落盘。 | [skills.sh](https://skills.sh/mattpocock/skills/domain-modeling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md) |
| `f-base-project-initializer` | `skills/workflow/f-base-project-initializer/` | 从固定 fan-base / fan-base-vben 模板克隆并重命名，生成可运行的 Fan 全栈新项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer/SKILL.md) |
| `f-base-project-initializer-cn` | `skills/workflow/f-base-project-initializer-cn/` | 中文指引：从固定 fan-base / fan-base-vben 模板初始化并重命名 Fan 全栈项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer-cn/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/workflow/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的项目强隔离、增量证据索引、可恢复运行与失败关闭质量门禁技能。 | 暂无 | [本仓库](../../.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
| `f-project-runtime-manager` | `skills/workflow/f-project-runtime-manager/` | 探测 Java/Spring Boot 与 Vue/Vite 项目结构，生成可移植的启停/状态脚本，不改原文件。 | 暂无 | [本仓库](../../.agents/skills/f-project-runtime-manager/SKILL.md) |
| `find-skills` | `skills/workflow/find-skills/` | 从开放 skills 生态检索并安装可扩展 Agent 能力的技能包。 | [skills.sh](https://skills.sh/vercel-labs/skills/find-skills) | [GitHub](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) |
| `grill-me` | `skills/workflow/grill-me/` | 启动一轮严厉质询会话，压力测试计划或设计直至达成共识。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-me) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) |
| `grill-with-docs` | `skills/workflow/grill-with-docs/` | 严厉质询方案的同时，用领域建模把 ADR 与词汇表边问边写下来。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-with-docs) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) |
| `grilling` | `skills/workflow/grilling/` | 一次只问一个问题，沿决策树严厉追问计划，直到达成共享理解。 | [skills.sh](https://skills.sh/mattpocock/skills/grilling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) |
| `improve-codebase-architecture` | `skills/workflow/improve-codebase-architecture/` | 扫描代码库找加深模块的机会，输出 HTML 报告并质询选定重构方向。 | [skills.sh](https://skills.sh/mattpocock/skills/improve-codebase-architecture) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) |
| `request-refactor-plan` | `skills/workflow/request-refactor-plan/` | 通过访谈产出小步可验证的重构计划，并可整理为 GitHub Issue。 | [skills.sh](https://skills.sh/mattpocock/skills/request-refactor-plan) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/deprecated/request-refactor-plan/SKILL.md) |

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

按用户项目名规范化为 kebab-case，派生前后端目录、Maven groupId 与数据库名；克隆两仓后改远程名为 fan-base、解除 upstream；批量迁移 pom 坐标与库名配置，保留 fan-server 模块与外部依赖；可衔接生成运行脚本与 AGENTS.md，并做启动验证。

#### 适用场景

基于 Fan 官方 Gitee 模板开新项目、批量改名与坐标迁移、初始化后希望一键生成启停脚本或确认前后端能启动时使用。

#### 主要覆盖内容

必需输入与命名派生、克隆重命名与远程策略、Maven/数据库迁移不变量、残留模板名检查、后端 clean-build、可选运行脚本与 AGENTS.md、启动验证清单。

#### 注意事项

目标目录非空禁止覆盖。未提供目标远程时不得推送。英文版与中文版流程一致，按对话语言选用。本 skill 为 Fan 本地自建，无 skills.sh / 公开 GitHub。

### `f-base-project-initializer-cn`

**路径**：`skills/workflow/f-base-project-initializer-cn/`

#### 核心能力

确认并规范化项目名后派生目录与坐标；拉取两模板仓、重命名远程并解除上游；迁移全部受控 pom 与数据库相关配置，保留 fan-server 可执行模块；可选生成根目录运行脚本与 AGENTS.md，并启动验证可运行应用。

#### 适用场景

中文协作下从 Fan 模板开新仓、改前后端目录名与 Maven/库名、需要初始化后生成启停脚本或验证能否启动时使用。

#### 主要覆盖内容

名称确认、双仓克隆与远程策略、Maven 与数据库迁移、残留模板名处理、后端构建、可选脚本与 AGENTS.md、启动验证阶段清单。

#### 注意事项

与英文版 `f-base-project-initializer` 同源流程，按用户语言选用其一即可，勿同时执行两套。非空目标目录不得覆盖；无用户远程时不推送。Fan 本地自建 skill。

### `f-enterprise-source-reverse-engineering`

**路径**：`skills/workflow/f-enterprise-source-reverse-engineering/`

#### 核心能力

按 Project 绑定不同源码根并构建源码、符号和业务三层持久索引；通过完整限定参数类型、调用可达性与已知表关联生成结构事实，把 Service、Repository、Model、Request 等名称信号限制为候选；支持带审核人和时间戳的负向证据安全写入、可信快照、失败阶段续跑、补证后独立终结，以及文件归属、方法调用者和业务规则关联接口与表查询。

#### 适用场景

适用于初始化或刷新两套大型 PHP 项目工作区、逐模块增量逆向、从失败阶段继续分析、为 PARTIAL 运行补齐人工证据后安全终结、查询文件归属或方法调用者、追踪规则关联接口与表、传播并复核过期证据、审计模块完成度，或依据已批准的双项目事实设计可追溯 Java 目标系统。

#### 主要覆盖内容

覆盖 A/B 根目录和事实读取隔离、源码与解析结果增量缓存、解析器版本失效、多模块追加归属及显式角色替换、路由到 Controller、验证、Service、持久化、事务和副作用的接口证据链、PRESENT 与 UNRESOLVED 及经审核的 NOT_APPLICABLE、真实哈希行号、STALE 传播、门禁候选与最终提交分离、完整自动管线及门禁尝试记录、JSON Schema 和十八项门禁。

#### 注意事项

核心脚本仅依赖 Python 标准库并兼容 Windows 与 Linux，Schema 和平台格式测试需安装测试依赖。独立门禁只产生候选结果，补证后必须使用同一运行 ID 的 --finalize 完成最终提交；继续运行会复核实际源码集合与哈希，发现变化时必须创建新运行。可信快照只供刚完成刷新且 token 匹配的单项目管线使用。PHP 解析仍是保守候选解析，动态调用、复杂语法、非 HTTP 入口及是否真正不适用仍需人工补证。

### `f-project-runtime-manager`

**路径**：`skills/workflow/f-project-runtime-manager/`

#### 核心能力

先分析仓库（构建工具、可执行模块、包管理器、dev/build 脚本、端口/profile 只读推断），再在 `scripts/` 下生成 start/stop/restart/status（多应用可聚合）脚本；配置外置到 `scripts/config/`，安全停进程（PID 优先，禁用 killall/pkill），启动前必编译。

#### 适用场景

用户要求生成项目启动管理脚本、本地启停管理器、前后端进程管理或统一启动脚本时使用，尤其是 Spring Boot + Vue 单仓或 monorepo。

#### 主要覆盖内容

管理根目录判定、后端/前端探测启发式、脚本文件布局与生成规则、dry-run 校验与完成时输出；细节见 reference.md 与 examples.md。

#### 注意事项

禁止使用固定模板或硬编码路径；禁止改动 application*.yml、package.json、pom.xml 等既有文件，仅新增 `scripts/`。幂等生成，再次运行先读已有脚本增量更新。Fan 本地自建 skill，无公开仓库。

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
