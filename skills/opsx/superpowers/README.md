# Opsx / Superpowers

Superpowers 工作流技能（/superpowers:*），与 commands/superpowers 对应

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `superpowers-brainstorming` | `skills/opsx/superpowers/superpowers-brainstorming/` | 创意与需求澄清：实现前先对齐意图与方案。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-brainstorming/SKILL.md) |
| `superpowers-dispatching-parallel-agents` | `skills/opsx/superpowers/superpowers-dispatching-parallel-agents/` | 把互不依赖的工作拆给并行子代理处理。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-dispatching-parallel-agents/SKILL.md) |
| `superpowers-executing-plans` | `skills/opsx/superpowers/superpowers-executing-plans/` | 按既有实现计划逐步执行并设检查点。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-executing-plans/SKILL.md) |
| `superpowers-finishing-a-development-branch` | `skills/opsx/superpowers/superpowers-finishing-a-development-branch/` | 实现完成后选择合并、PR 或清理的收尾路径。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-finishing-a-development-branch/SKILL.md) |
| `superpowers-receiving-code-review` | `skills/opsx/superpowers/superpowers-receiving-code-review/` | 严谨消化代码审查意见并落地修改。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-receiving-code-review/SKILL.md) |
| `superpowers-requesting-code-review` | `skills/opsx/superpowers/superpowers-requesting-code-review/` | 在合并前发起结构化代码审查请求。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-requesting-code-review/SKILL.md) |
| `superpowers-subagent-driven-development` | `skills/opsx/superpowers/superpowers-subagent-driven-development/` | 按计划为每个任务派生子代理并两阶段复查。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-subagent-driven-development/SKILL.md) |
| `superpowers-systematic-debugging` | `skills/opsx/superpowers/superpowers-systematic-debugging/` | 系统化排查缺陷：先复现取证再改代码。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-systematic-debugging/SKILL.md) |
| `superpowers-test-driven-development` | `skills/opsx/superpowers/superpowers-test-driven-development/` | 强制先写失败测试再写实现的 TDD 节奏。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-test-driven-development/SKILL.md) |
| `superpowers-using-git-worktrees` | `skills/opsx/superpowers/superpowers-using-git-worktrees/` | 用 git worktree 隔离功能开发目录。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-using-git-worktrees/SKILL.md) |
| `superpowers-using-superpowers` | `skills/opsx/superpowers/superpowers-using-superpowers/` | 会话开始时建立“先调用相关技能”的工作纪律。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-using-superpowers/SKILL.md) |
| `superpowers-verification-before-completion` | `skills/opsx/superpowers/superpowers-verification-before-completion/` | 声称完成前必须跑验证命令并核对输出。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-verification-before-completion/SKILL.md) |
| `superpowers-writing-plans` | `skills/opsx/superpowers/superpowers-writing-plans/` | 把已明确的需求写成可执行的分步实现计划。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-writing-plans/SKILL.md) |
| `superpowers-writing-skills` | `skills/opsx/superpowers/superpowers-writing-skills/` | 编写、修改并验证 Agent Skill 本身。 | 暂无 | [本仓库](../../../.agents/skills/superpowers-writing-skills/SKILL.md) |

## 详细介绍

### `superpowers-brainstorming`

**路径**：`skills/opsx/superpowers/superpowers-brainstorming/`

#### 核心能力

通过结构化提问与可视化探索功能边界，再进入计划。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

新功能、模糊需求或设计分歧较大时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖头脑风暴流程、视觉伴侣与决策沉淀方式。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

未澄清前不要直接写代码；用户指令优先于技能默认。与用户显式指令冲突时以用户指令为准。

### `superpowers-dispatching-parallel-agents`

**路径**：`skills/opsx/superpowers/superpowers-dispatching-parallel-agents/`

#### 核心能力

识别可并行任务、分派与汇总结果，缩短墙钟时间。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

多模块独立调研或修改时可使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖任务拆分、隔离与结果合并。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

有共享状态或顺序依赖时不要强行并行。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-executing-plans`

**路径**：`skills/opsx/superpowers/superpowers-executing-plans/`

#### 核心能力

加载计划、按任务推进、失败即停，完成后进入收尾技能。并给出可执行的步骤与约束说明。

#### 适用场景

已有书面计划、希望本会话连续落地时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖执行节奏、验证步骤与求助条件。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

有子代理时更推荐 subagent-driven-development。与用户显式指令冲突时以用户指令为准。

### `superpowers-finishing-a-development-branch`

**路径**：`skills/opsx/superpowers/superpowers-finishing-a-development-branch/`

#### 核心能力

在测试通过后给出集成选项并执行用户选择。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

功能做完、准备合流或关闭分支时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖验证、选项呈现与收尾动作。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

未验证通过不要宣称完成或强推远程。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-receiving-code-review`

**路径**：`skills/opsx/superpowers/superpowers-receiving-code-review/`

#### 核心能力

区分必改与建议，验证技术正确性后再改，避免盲从。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

收到 PR/审查评论需要处理时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖意见分类、争议处理与回归验证。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

不清楚的反馈先问清，不把错误建议直接合入。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-requesting-code-review`

**路径**：`skills/opsx/superpowers/superpowers-requesting-code-review/`

#### 核心能力

整理变更说明与审查焦点，便于审查者高效反馈。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

完成大功能、准备合并或需要第二双眼睛时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖审查请求内容与关注点清单。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

审查意见回来后配合 receiving-code-review 处理。与用户显式指令冲突时以用户指令为准。

### `superpowers-subagent-driven-development`

**路径**：`skills/opsx/superpowers/superpowers-subagent-driven-development/`

#### 核心能力

主代理编排，子代理实现，降低上下文污染与遗漏。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

多任务独立、适合并行或严格分任务质检时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖派发、审查与合入节奏。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

子代理需给足路径与验收标准，避免口头含糊委托。与用户显式指令冲突时以用户指令为准。

### `superpowers-systematic-debugging`

**路径**：`skills/opsx/superpowers/superpowers-systematic-debugging/`

#### 核心能力

强调根因追踪、防回归与分层验证，避免盲改。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

任何 bug、测试失败或异常行为在提修复前使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖取证、假设检验与防御性加固思路。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

禁止跳过复现直接大面积重写。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-test-driven-development`

**路径**：`skills/opsx/superpowers/superpowers-test-driven-development/`

#### 核心能力

用红-绿-重构约束改动，降低无测试直改生产代码风险。并给出可执行的步骤与约束说明。

#### 适用场景

功能开发与缺陷修复在可测代码库中优先使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖测试先行、最小实现与重构边界。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

若环境无法运行测试，应先说明限制再调整策略。与用户显式指令冲突时以用户指令为准。

### `superpowers-using-git-worktrees`

**路径**：`skills/opsx/superpowers/superpowers-using-git-worktrees/`

#### 核心能力

创建或确认独立工作树，避免污染主工作区。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

并行功能、执行计划前需要干净目录时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 worktree 创建、路径约定与清理注意点。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

不要在未隔离的脏主树上硬开大改动。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-using-superpowers`

**路径**：`skills/opsx/superpowers/superpowers-using-superpowers/`

#### 核心能力

要求在响应前检查并调用适用技能，统一跨工具行为。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

几乎所有会话开场都应考虑；子代理执行专项任务时可跳过。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖技能优先级、调用时机与平台差异说明。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

用户显式指令始终高于技能默认策略。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `superpowers-verification-before-completion`

**路径**：`skills/opsx/superpowers/superpowers-verification-before-completion/`

#### 核心能力

禁止在未验证时宣告 fixed/passing；以命令结果为准。并给出可执行的步骤与约束说明。

#### 适用场景

准备提交、开 PR 或回复“已修好”之前使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖验证命令选择与失败处理。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

验证失败则继续修，不得用“应该没问题”代替。与用户显式指令冲突时以用户指令为准。

### `superpowers-writing-plans`

**路径**：`skills/opsx/superpowers/superpowers-writing-plans/`

#### 核心能力

产出含精确路径、命令与验收的任务清单，便于代理执行。并给出可执行的步骤与约束说明。

#### 适用场景

规格已清、准备开工或交给执行技能前使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖计划结构、任务粒度、禁止空洞步骤等约束。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

计划默认写在约定 plans 目录；本工作区可将计划放根 docs。与用户显式指令冲突时以用户指令为准。

### `superpowers-writing-skills`

**路径**：`skills/opsx/superpowers/superpowers-writing-skills/`

#### 核心能力

指导 SKILL.md 结构、可测性与落地前自检。并给出可执行的步骤与约束说明。

#### 适用场景

创建新技能或大改现有技能时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖技能写作原则、测试思路与示例。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

技能应可执行可验证，避免只写口号式描述。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。
