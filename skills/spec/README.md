# 规范 / Spec

通用规格文档技能（非 OpenSpec 套件）

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `create-agentsmd` | `skills/spec/create-agentsmd/` | 按 agents.md 规范为仓库生成面向编码 Agent 的 AGENTS.md 上下文文件。 | [skills.sh](https://skills.sh/github/awesome-copilot/create-agentsmd) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/create-agentsmd/SKILL.md) |
| `create-specification` | `skills/spec/create-specification/` | 编写面向生成式 AI 消费的、结构清晰的解决方案规格说明文件。 | [skills.sh](https://skills.sh/github/awesome-copilot/create-specification) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/create-specification/SKILL.md) |

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
