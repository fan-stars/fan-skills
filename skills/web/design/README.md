# Web / 设计

前端视觉设计与 Web 界面规范审查

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `extract-design-system` | `skills/web/design/extract-design-system/` | 从任意公开网站逆向提取设计 token（配色/字体/间距/圆角/阴影）生成起步 token 文件。 | [skills.sh](https://skills.sh/arvindrk/extract-design-system/extract-design-system) | [GitHub](https://github.com/arvindrk/extract-design-system/blob/main/skills/extract-design-system/SKILL.md) |
| `finesse-brief` | `skills/web/design/finesse-brief/` | Workbench 架构师：把模糊一句话收成可构建规格。 | 暂无 | [本仓库](../../../.agents/skills/finesse-brief/SKILL.md) |
| `finesse-term` | `skills/web/design/finesse-term/` | 把口语化界面描述译成可发给代理的准确说法。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/finesse-term/SKILL.md) |
| `finesse-ui` | `skills/web/design/finesse-ui/` | 高工艺 Web/H5 界面实现：品牌向与动效向。 | 暂无 | [本仓库](../../../.agents/skills/finesse-ui/SKILL.md) |
| `frame-smith` | `skills/web/design/frame-smith/` | 用 Remotion 做电影感宣传短片合成。。用于目录浏览与选型。 | 暂无 | [本仓库](../../../.agents/skills/frame-smith/SKILL.md) |
| `frontend-design` | `skills/web/design/frontend-design/` | 做有辨识度的前端视觉设计：排版、调色与布局避免模板感默认解。 | [skills.sh](https://skills.sh/anthropics/skills/frontend-design) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) |
| `web-design-guidelines` | `skills/web/design/web-design-guidelines/` | 对照最新 Web Interface Guidelines 审查 UI 代码的可访问性与体验。 | [skills.sh](https://skills.sh/vercel-labs/agent-skills/web-design-guidelines) | [GitHub](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) |

## 详细介绍

### `extract-design-system`

**路径**：`skills/web/design/extract-design-system/`

#### 核心能力

用 Playwright 抓取公开网站，产出 `design-system/tokens.json` 与 `tokens.css`（W3C 兼容），支持仅提取、缓存重生成（init）与读取现有 token；也提供 MCP server 暴露同名工具调用。

#### 适用场景

想以某网站视觉为起点初始化项目设计系统、快速得到配色与排版 token，或为设计还原提供基线时使用。适合初始化而非像素级复刻。

#### 主要覆盖内容

提取工作流、raw/normalized 中间产物与 tokens 产物说明、仅提取与 init 两种模式，以及不覆盖既有样式、不臆造组件的安全边界。

#### 注意事项

需 Node 20+ 与 Playwright chromium。结果用于初始化，不应视为完整或权威；修改现有 app 代码/样式前必须先征得确认。与 `frontend-design`、`web-design-guidelines` 配合更佳。

### `finesse-brief`

**路径**：`skills/web/design/finesse-brief/`

#### 核心能力

在界面还不存在时澄清工作台类型、领域与交接物。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

新产品工作台、复杂后台从 0 构思时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖发现提问、语法与 handoff 产物。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

先 brief 再交给 UI 实现技能，避免边做边猜。与用户显式指令冲突时以用户指令为准。

### `finesse-term`

**路径**：`skills/web/design/finesse-term/`

#### 核心能力

检索 Web/H5 术语库，补全用户叫不出名的控件与状态。并给出可执行的步骤与约束说明。

#### 适用场景

任何轮次用户用大白话描述界面效果或故障时可用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖术语检索、说法层输出与多端词库。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

输出应可直接粘贴给实现代理，不要只堆名词解释。与用户显式指令冲突时以用户指令为准。

### `finesse-ui`

**路径**：`skills/web/design/finesse-ui/`

#### 核心能力

强调真实视觉锚点、有克制的动效与反廉价设计检查。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

落地页、品牌站、作品集或高质量产品壳时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖设计 DNA、动效、审计与示例库。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

若已有设计系统，优先遵循现有体系而非另起炉灶。与用户显式指令冲突时以用户指令为准。

### `frame-smith`

**路径**：`skills/web/design/frame-smith/`

#### 核心能力

提供镜头结构、特效菜单与运行环境检查，产出可渲染成片。并给出可执行的步骤与约束说明。

#### 适用场景

需要产品宣传片、主题翻转或数据叙事短视频时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖节拍结构、特效目录、声音与预检脚本。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

先确认运行时依赖，再堆特效；避免无预检直接渲染失败。与用户显式指令冲突时以用户指令为准。

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
