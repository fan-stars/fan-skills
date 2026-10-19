# Opsx / OpenSpec

OpenSpec CLI 新技能套件（/opsx:*），与 commands/opsx 对应

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `openspec-apply-change` | `skills/opsx/openspec/openspec-apply-change/` | 按 OpenSpec change 的 tasks 逐步实现代码。 | 暂无 | [本仓库](../../../.agents/skills/openspec-apply-change/SKILL.md) |
| `openspec-archive-change` | `skills/opsx/openspec/openspec-archive-change/` | 归档已完成的 OpenSpec change 并同步主规格。 | 暂无 | [本仓库](../../../.agents/skills/openspec-archive-change/SKILL.md) |
| `openspec-bulk-archive-change` | `skills/opsx/openspec/openspec-bulk-archive-change/` | 批量归档多个已完成的 OpenSpec change。 | 暂无 | [本仓库](../../../.agents/skills/openspec-bulk-archive-change/SKILL.md) |
| `openspec-continue-change` | `skills/opsx/openspec/openspec-continue-change/` | 继续推进进行中的 OpenSpec change 下一工件。 | 暂无 | [本仓库](../../../.agents/skills/openspec-continue-change/SKILL.md) |
| `openspec-explore` | `skills/opsx/openspec/openspec-explore/` | OpenSpec 探索模式：在动手实现前澄清需求与方案。 | 暂无 | [本仓库](../../../.agents/skills/openspec-explore/SKILL.md) |
| `openspec-ff-change` | `skills/opsx/openspec/openspec-ff-change/` | 快进生成实现前所需的全部 OpenSpec 工件。 | 暂无 | [本仓库](../../../.agents/skills/openspec-ff-change/SKILL.md) |
| `openspec-new-change` | `skills/opsx/openspec/openspec-new-change/` | 创建新的 OpenSpec change 脚手架与元数据。 | 暂无 | [本仓库](../../../.agents/skills/openspec-new-change/SKILL.md) |
| `openspec-onboard` | `skills/opsx/openspec/openspec-onboard/` | 引导完成一轮 OpenSpec 工作流上手体验。 | 暂无 | [本仓库](../../../.agents/skills/openspec-onboard/SKILL.md) |
| `openspec-propose` | `skills/opsx/openspec/openspec-propose/` | 一键生成 OpenSpec change 的完整提案工件。 | 暂无 | [本仓库](../../../.agents/skills/openspec-propose/SKILL.md) |
| `openspec-sync-specs` | `skills/opsx/openspec/openspec-sync-specs/` | 在不归档的情况下把 delta specs 同步到主规格。 | 暂无 | [本仓库](../../../.agents/skills/openspec-sync-specs/SKILL.md) |
| `openspec-update-change` | `skills/opsx/openspec/openspec-update-change/` | 修订已有 OpenSpec change 的规划工件并保持一致。 | 暂无 | [本仓库](../../../.agents/skills/openspec-update-change/SKILL.md) |
| `openspec-verify-change` | `skills/opsx/openspec/openspec-verify-change/` | 在归档前核对实现与 change 工件是否一致。 | 暂无 | [本仓库](../../../.agents/skills/openspec-verify-change/SKILL.md) |

## 详细介绍

### `openspec-apply-change`

**路径**：`skills/opsx/openspec/openspec-apply-change/`

#### 核心能力

读取 apply 指令与任务列表，驱动实现并回写完成状态。并给出可执行的步骤与约束说明。

#### 适用场景

提案已就绪、准备编码落地时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 apply 指令、任务勾选与实现约束。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

只实现已批准范围内的任务，避免顺手扩 scope。与用户显式指令冲突时以用户指令为准。

### `openspec-archive-change`

**路径**：`skills/opsx/openspec/openspec-archive-change/`

#### 核心能力

将 delta specs 合入主 specs，并移动 change 到 archive。

#### 适用场景

验证通过、变更已上线或可关闭时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 archive 命令、规格同步与收尾检查。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

未验证通过勿归档；归档后主 specs 即新基线。与用户显式指令冲突时以用户指令为准。

### `openspec-bulk-archive-change`

**路径**：`skills/opsx/openspec/openspec-bulk-archive-change/`

#### 核心能力

在并行变更收尾时一次处理多个 archive，减少重复操作。并给出可执行的步骤与约束说明。

#### 适用场景

有多条已完成 change 待清理时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖批量选择、失败隔离与结果汇总。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

逐条确认可归档状态，避免把未完成项卷进去。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `openspec-continue-change`

**路径**：`skills/opsx/openspec/openspec-continue-change/`

#### 核心能力

根据 status 找到下一个 ready artifact 并产出内容。并给出可执行的步骤与约束说明。

#### 适用场景

中途暂停后恢复、或需要补齐下一份文档时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 continue 流程与依赖阻塞处理。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

若被未请求的前置工件阻塞，应先征得同意再扩展。与用户显式指令冲突时以用户指令为准。

### `openspec-explore`

**路径**：`skills/opsx/openspec/openspec-explore/`

#### 核心能力

提供探索姿态下的对话、可视化与 OpenSpec 上下文读取，帮助在写提案前理清问题边界。

#### 适用场景

适合需求模糊、需要对比方案或盘点现状时使用，例如 /opsx:explore 会话。

#### 主要覆盖内容

覆盖 explore 流程、artifact 捕获边界与不自动落地实现的护栏。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

探索模式默认不写业务代码；要落地需另行确认并创建 change。与用户显式指令冲突时以用户指令为准。

### `openspec-ff-change`

**路径**：`skills/opsx/openspec/openspec-ff-change/`

#### 核心能力

在已明确意图时批量创建提案相关 artifact，减少逐步询问。并给出可执行的步骤与约束说明。

#### 适用场景

适合目标清晰、希望尽快进入实现门禁的场景。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 ff-change 流程与工件齐套检查。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

快进不等于跳过评审；实现前仍应核对 proposal/tasks。与用户显式指令冲突时以用户指令为准。

### `openspec-new-change`

**路径**：`skills/opsx/openspec/openspec-new-change/`

#### 核心能力

用 CLI 生成带 .openspec.yaml 的 change 目录，避免手建漏文件。

#### 适用场景

开始一项受控变更、尚未写提案正文时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 new change 命名、store 参数与脚手架布局。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

不要手建 openspec/changes 目录；必须走该流程或 CLI。与用户显式指令冲突时以用户指令为准。

### `openspec-onboard`

**路径**：`skills/opsx/openspec/openspec-onboard/`

#### 核心能力

串联讲解与实操，帮助新用户走完从想到归档的闭环。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

团队首次引入 OpenSpec 或培训新成员时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 onboarding 叙事、命令顺序与常见坑。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

演示环境尽量用样例 change，避免污染真实主规格。与用户显式指令冲突时以用户指令为准。

### `openspec-propose`

**路径**：`skills/opsx/openspec/openspec-propose/`

#### 核心能力

串联新建 change 与 proposal/design/tasks 等工件生成，加快提案起步。

#### 适用场景

当已想清楚要做什么、希望快速产出可评审提案时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 propose 命令流程与工件依赖顺序。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

生成后仍需人工审阅提案内容，勿把草稿当已批准规格。与用户显式指令冲突时以用户指令为准。

### `openspec-sync-specs`

**路径**：`skills/opsx/openspec/openspec-sync-specs/`

#### 核心能力

适用于需要提前更新主 specs、但 change 仍继续的场景。并给出可执行的步骤与约束说明。

#### 适用场景

主规格需先行对齐、或分阶段合入时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 sync-specs 流程与冲突处理提示。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

同步后检查主 specs 是否仍与进行中 change 语义一致。与用户显式指令冲突时以用户指令为准。

### `openspec-update-change`

**路径**：`skills/opsx/openspec/openspec-update-change/`

#### 核心能力

在需求漂移时更新 proposal/design/tasks，避免文档互相矛盾。

#### 适用场景

实现中发现范围变化、需要改计划时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖更新顺序与一致性检查要点。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

更新后重新跑 status/validate，确认无残留冲突描述。与用户显式指令冲突时以用户指令为准。

### `openspec-verify-change`

**路径**：`skills/opsx/openspec/openspec-verify-change/`

#### 核心能力

检查任务完成度、行为与规格偏差，给出可归档结论。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

准备 archive 前或怀疑实现漏项时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖验证清单与常见不一致类型。细节以仓库内 SKILL.md 与引用文档为准。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

验证失败应回到 apply/update，而不是强行归档。与用户显式指令冲突时以用户指令为准。
