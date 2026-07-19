# Web / 设计

前端视觉设计与 Web 界面规范审查

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `frontend-design` | `skills/web/design/frontend-design/` | 做有辨识度的前端视觉设计：排版、调色与布局避免模板感默认解。 | [skills.sh](https://skills.sh/anthropics/skills/frontend-design) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) |
| `web-design-guidelines` | `skills/web/design/web-design-guidelines/` | 对照最新 Web Interface Guidelines 审查 UI 代码的可访问性与体验。 | [skills.sh](https://skills.sh/vercel-labs/agent-skills/web-design-guidelines) | [GitHub](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) |

## 详细介绍

### `frontend-design`

**路径**：`skills/web/design/frontend-design/`

#### 核心能力

以设计主导视角做有主见的美学选择：锚定题材与受众、英雄区命题、字体配对、氛围背景与动效层次，刻意规避常见 AI 模板审美。

#### 适用场景

新建页面或重塑现有 UI、需要独特视觉方向而非通用后台皮肤、落地页与品牌向界面设计时启用。

#### 主要覆盖内容

题材锚定、英雄区原则、字体与色彩方向、减少卡片/杂讯、用动效建立层级等设计原则。

#### 注意事项

若已有设计系统，应服从现有语言。先钉死产品题材再开做；不要堆无意义的渐变与徽章。

### `web-design-guidelines`

**路径**：`skills/web/design/web-design-guidelines/`

#### 核心能力

每次审查前拉取 Vercel web-interface-guidelines 最新规则，按文件检查并输出简洁的 file:line 发现项。

#### 适用场景

用户要求 review UI、查无障碍、审计设计/UX、对照最佳实践检查站点时使用。

#### 主要覆盖内容

拉取最新指南、读取用户指定文件或模式、按全部规则对照检查，并按规定格式输出；未指定范围时先询问审查文件。

#### 注意事项

必须用 WebFetch 拉取新鲜远程规则，勿只靠记忆版清单。输出保持指南要求的简洁 file:line 格式，便于逐条修复。
