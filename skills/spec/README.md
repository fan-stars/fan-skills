# 规范 / Spec

OpenSpec 与规格文档相关 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `create-agentsmd` | `skills/spec/create-agentsmd/` | 按 agents.md 规范为仓库生成面向编码 Agent 的 AGENTS.md 上下文文件。 | [skills.sh](https://skills.sh/github/awesome-copilot/create-agentsmd) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/create-agentsmd/SKILL.md) |
| `create-specification` | `skills/spec/create-specification/` | 编写面向生成式 AI 消费的、结构清晰的解决方案规格说明文件。 | [skills.sh](https://skills.sh/github/awesome-copilot/create-specification) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/create-specification/SKILL.md) |
| `openspec-archiving` | `skills/spec/openspec-archiving/` | 归档已完成变更，并将规范差异合并进长期有效的 living specs。 | [skills.sh](https://skills.sh/forztf/open-skilled-sdd/openspec-archiving) | [GitHub](https://github.com/forztf/open-skilled-sdd/blob/main/skills/openspec-archiving/SKILL.md) |
| `openspec-context-loading` | `skills/spec/openspec-context-loading/` | 发现并加载项目 specs、进行中变更与需求，回答「现在有什么」。 | [skills.sh](https://skills.sh/forztf/open-skilled-sdd/openspec-context-loading) | [GitHub](https://github.com/forztf/open-skilled-sdd/blob/main/skills/openspec-context-loading/SKILL.md) |
| `openspec-implementation` | `skills/spec/openspec-implementation/` | 按已批准提案逐项实现任务，每步测试验证后再勾选完成。 | [skills.sh](https://skills.sh/forztf/open-skilled-sdd/openspec-implementation) | [GitHub](https://github.com/forztf/open-skilled-sdd/blob/main/skills/openspec-implementation/SKILL.md) |
| `openspec-proposal-creation` | `skills/spec/openspec-proposal-creation/` | 用英文 OpenSpec 流程创建提案、任务清单与 EARS 风格规范差异。 | [skills.sh](https://skills.sh/forztf/open-skilled-sdd/openspec-proposal-creation) | [GitHub](https://github.com/forztf/open-skilled-sdd/blob/main/skills/openspec-proposal-creation/SKILL.md) |
| `openspec-proposal-creation-cn` | `skills/spec/openspec-proposal-creation-cn/` | 中文 OpenSpec 提案：proposal、tasks.json 与规范差异，面向规划与审批。 | [skills.sh](https://skills.sh/forztf/open-skilled-sdd/openspec-proposal-creation-cn) | [GitHub](https://github.com/forztf/open-skilled-sdd/blob/main/skills/openspec-proposal-creation-cn/SKILL.md) |

## 详细介绍

### `create-agentsmd`

**路径**：`skills/spec/create-agentsmd/`

#### 核心能力

指导在仓库根（或 monorepo 子项目）创建完整、准确的 AGENTS.md：项目概览、技术栈、结构、命令、约定与 Agent 注意事项，作为给人看的 README 的补充。

#### 适用场景

新建或补齐 Agent 指引、让多种编码工具共享同一套仓库约定、需要把构建/测试/风格规则写成机器友好说明时使用。

#### 主要覆盖内容

AGENTS.md 定位与原则、推荐章节结构、与 README 的分工、跨 20+ 工具兼容的开放格式写法。

#### 注意事项

内容面向 Agent 技术细节，勿整份替代人类 README。结构可按项目裁剪，但应放在可预期路径并保持可维护。

### `create-specification`

**路径**：`skills/spec/create-specification/`

#### 核心能力

按模板在 `/spec/` 下创建自包含规格：需求、约束、接口、术语与示例边界，使用明确无歧义语言与结构化 Markdown，便于后续 AI 实现。

#### 适用场景

需要为 schema、工具、数据、基础设施、流程、架构或设计等主题立规格，或要把口头需求固化成机器可读文档时启用。

#### 主要覆盖内容

命名约定 `spec-[purpose]-….md`、front matter、章节模板、AI-ready 写作实践（精确措辞、区分需求/约束/建议、定义缩写）。

#### 注意事项

规格须自包含，少依赖外部上下文。命名 purpose 须落在约定集合内；保存路径与格式需严格遵循 skill 模板。

### `openspec-archiving`

**路径**：`skills/spec/openspec-archiving/`

#### 核心能力

在实现与部署确认后，合并 ADDED/MODIFIED/REMOVED 到 `spec/specs`，并把 change 目录移入带时间戳的 archive，校验 living spec 结构。

#### 适用场景

变更已上线或可归档、需要「openspec archive / merge specs / finalize」时使用。

#### 主要覆盖内容

完成度检查、delta 审阅、时间戳归档目录、三类合并操作、移动 change 与结构校验清单。

#### 注意事项

仍有未完成任务或尚未部署时不要归档。归档表示完成与部署语义，合并 living specs 前须先取得用户明确同意。

### `openspec-context-loading`

**路径**：`skills/spec/openspec-context-loading/`

#### 核心能力

列出 living specs、active/archived changes，搜索能力与 Requirement，汇总项目规范上下文，支撑后续提案或实现。

#### 适用场景

用户询问现有规范、进行中或已归档变更、系统能力边界，或需要「spec 里有什么」这类项目上下文发现时使用。

#### 主要覆盖内容

发现命令模式（find/grep/tree/ls）、搜索 Requirement 与能力目录、阅读后摘要的基本套路，避免无目标整库灌入。

#### 注意事项

先搜索再精读，避免整库灌入上下文。本仓库若忽略 `spec/`，仍按本地约定路径操作。

### `openspec-implementation`

**路径**：`skills/spec/openspec-implementation/`

#### 核心能力

读取 proposal/tasks/spec deltas，用 Todo 跟踪，严格顺序执行：实现→测试→验证→更新规范（如需）→标记实现完成。

#### 适用场景

用户要求 openspec implement、执行 tasks、按批准计划开发功能时启用。

#### 主要覆盖内容

加载提案与任务、Todo 跟踪、按序实现与验收、必要时更新 living specs、标记实现完成等完整检查清单。

#### 注意事项

禁止跳过任务或未经验证就标完成。每一项完成后应留下可观察证据（测试、行为或产物）再进入下一项。

### `openspec-proposal-creation`

**路径**：`skills/spec/openspec-proposal-creation/`

#### 核心能力

脚手架 change 目录，产出 proposal.md、tasks.md 与 ADDED/MODIFIED/REMOVED 的 spec deltas，供审批后再实现。

#### 适用场景

规划新功能、破坏性变更或架构更新，触发 create proposal / spec feature 等英文流程时使用。

#### 主要覆盖内容

审阅现有规范、生成 change-id、Why/What/Impact、任务清单、EARS 需求写法与结构校验。

#### 注意事项

中文团队日常规划优先 `openspec-proposal-creation-cn`（tasks.json 等差异）。提案需用户批准后再进入实现。

### `openspec-proposal-creation-cn`

**路径**：`skills/spec/openspec-proposal-creation-cn/`

#### 核心能力

按中文工作流生成变更目录、proposal.md、tasks.json 与 spec-delta（ADDED/MODIFIED/REMOVED），并用清单校验后提交用户审批。

#### 适用场景

用户说「openspec提案」「规划变更」「新功能/新需求」等中文触发词，要用规范驱动方式开干前先立提案时使用。

#### 主要覆盖内容

变更 ID 约定、目录脚手架、提案三要素、tasks.json 模板、规范差异与展示审批步骤。

#### 注意事项

与英文版提案 skill 并行存在，字段/任务格式以中文版模板为准。未审批前不要开始大规模实现。
