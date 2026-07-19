# 工作流

规划质询、领域建模、架构词汇与技能发现

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `codebase-design` | `skills/workflow/codebase-design/` | 用「深模块」词汇设计小接口、大行为、可测试的代码接缝与边界。 | [skills.sh](https://skills.sh/mattpocock/skills/codebase-design) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) |
| `domain-modeling` | `skills/workflow/domain-modeling/` | 主动打磨项目领域模型：统一语言、边界场景与架构决策落盘。 | [skills.sh](https://skills.sh/mattpocock/skills/domain-modeling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md) |
| `f-project-runtime-manager` | `skills/workflow/f-project-runtime-manager/` | 探测 Java/Spring Boot 与 Vue/Vite 项目结构，生成可移植的启停/状态脚本，不改原文件。 | 暂无 | [本仓库](../../.agents/skills/f-project-runtime-manager/SKILL.md) |
| `find-skills` | `skills/workflow/find-skills/` | 从开放 skills 生态检索并安装可扩展 Agent 能力的技能包。 | [skills.sh](https://skills.sh/vercel-labs/skills/find-skills) | [GitHub](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) |
| `grill-me` | `skills/workflow/grill-me/` | 启动一轮严厉质询会话，压力测试计划或设计直至达成共识。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-me) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) |
| `grill-with-docs` | `skills/workflow/grill-with-docs/` | 严厉质询方案的同时，用领域建模把 ADR 与词汇表边问边写下来。 | [skills.sh](https://skills.sh/mattpocock/skills/grill-with-docs) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) |
| `grilling` | `skills/workflow/grilling/` | 一次只问一个问题，沿决策树严厉追问计划，直到达成共享理解。 | [skills.sh](https://skills.sh/mattpocock/skills/grilling) | [GitHub](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) |

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
