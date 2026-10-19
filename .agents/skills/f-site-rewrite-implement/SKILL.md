---
name: f-site-rewrite-implement
description: >-
  Portable site-rewrite workflow after f-site-rewrite-init (which copies
  scaffold/ to repo-root site-rewrite/). Playwright observations, source/API
  indexes, UI-library-first, skills analysis, grill-with-docs, OpenSpec gates,
  per-module ≥95% match then Chinese commit, archive docs. Triggers
  "f-site-rewrite", "按重构工作流", "对照旧站重构".
---

# f-site-rewrite-implement

在 **`f-site-rewrite-init`** 就绪后执行。用户**没有**明确要求跳过某步骤时，**必须**按下列步骤完整执行。

配置路径：`site-rewrite/refactor.config.yaml`。若项目根**没有** `site-rewrite/`，先跑 **`f-site-rewrite-init`**（会从该 skill 的 `scaffold/` 复制到项目根）。勿手写空目录代替 init。

每次开始前先读索引：`site-rewrite/indexes/`（已读源码 / 观测 / 模块状态 / 拟用 skills / **数据接口调用**），避免重复摸索。

## Master checklist（不得跳过）

```
Site Rewrite Progress:
- [ ] 1. Playwright：本站 / 要重构站 / 参考站 → observations + 更新索引
- [ ] 2. 阅读对应源码（如有）→ 更新 sources-read 索引
- [ ] 3. 阅读重构过程文档与踩坑
- [ ] 4. UI 库优先；不满足则停下征得同意后再自定义，否则停止
- [ ] 5. 分析本次可能用到的 skills → 写入索引并 Read 必用项
- [ ] 6. 需求不明 → grill-with-docs；禁止瞎猜
- [ ] 7. grill-with-docs 结束后归档
- [ ] 8. OpenSpec 提案（前 5 点门禁；模块 ≥95% 对比；中文 commit）
- [ ] 9. 提案批准后 openspec-implementation，按序完成任务
- [ ] 10. 过程文档与踩坑归档到 site-rewrite/playbooks
```

以下编号与约定步骤一致。

---

## 1. 通过 Playwright MCP 访问本站、要重构的网站、参考的网站记录相关的信息，可以输出到对应的

- 使用 **Playwright MCP**（可用的 Playwright 工具；用户写作 `/palywright` 时同此）。
- 顺序建议：`rewriteSite` → `legacySite` → 每个 `referenceSites[]`。
- 鉴权来自 `site-rewrite/secrets.local.env`（经配置 `auth.secretsFile`）。
- 输出：`site-rewrite/observations/`（或配置 `docs.observationsDir`）。
- 命名：`<siteId>-<pageOrModule>-<YYYYMMDD>.md`（可附截图）。
- 观测须尽量记录后续评分用的视觉项：**字体 / 背景 / 边距 / 大小 / 边框 / 圆角 / 阴影 / 主色 / 图标图 / hover / 激活态 / 角标 / 动效 / 透叠 / 溢出** 等（见观测模板与 [match-rubric.md](match-rubric.md)）。
- 写入后更新 `indexes/observations-index.yaml`。
- **禁止**把密钥写入 observations。

模板：[observation-template.md](observation-template.md)。

---

## 2. 在参考对应的源码的(如有)

- 先查 `indexes/sources-read.yaml`：已有条目则打开其 `path` / `notes` 速览，再按需补读。
- 打开 `sourceTrees[]` 中与本模块相关的模板 / 组件 / CSS / 接口。
- **只读**；未经用户明确允许不得改旧站源码。
- 读完后 **append/更新** `indexes/sources-read.yaml`（path、moduleIds、summary、lastRead）。
- 示例项目同理更新 `indexes/examples-read.yaml`。

### 2.1 数据接口（如有配置）

- 配置项：`dataApis[]`（中文名：**数据接口**）——源平台取数 API，与访客前台 `legacySite` 区分。
- 先查 `indexes/data-api-calls.yaml`：同一 `apiId + method + path` 已有记录则先读 `recordFile`，避免重复瞎请求。
- 新请求或新抓包后：
  1. 按 [data-api-record-template.md](../f-site-rewrite-init/data-api-record-template.md) 写入 `site-rewrite/data-apis/`（或配置 `docs.dataApisDir`）；
  2. 更新 `indexes/data-api-calls.yaml`；
  3. 记录 **URL 形态、请求参数、响应字段/脱敏样例**；
  4. **禁止**写入 token / cookie / 密码。
- 映射访客 VO 时对照已有记录中的字段说明与易错语义。

---

## 3. 阅读重构过程的文档和对应的坑（避免后续再次采坑）

- 阅读 `site-rewrite/playbooks/`、`docs.pitfallsFile`、可选 `docs.contextFile`。
- 若仓库有 `AGENTS.md` 且含 UI 强制工作流，**一并遵守**。
- 适用的坑记入本轮笔记；实现时规避。

---

## 4. 如果指定了使用的UI库（会有对应的skills 或者 对应的文档），则必须优先使用对应的UI组件，尽量不要自定义组件，实在不能满足时，直接停下来或者交互式提问征得用户同意后再自定义组件，否则就停止

- `target.uiLibrary` 非空 → 先读 `skills.uiLibrary` 与相关文档。
- **必须优先** UI 库组件；**尽量不要**自定义。
- 无法满足：停止编码 → 说明缺口与方案 → **明确同意**后再自定义；未同意 → **停止**。

---

## 5. 分析本次可能用到的 skills

在 UI 库门禁之后、grill / 提案之前，**必须**盘点本轮会用到的 Agent Skills，并落盘：

1. 扫描工作区 `.agents/skills/`（及用户个人 skills，若可知）的 `name` / `description`。  
2. 结合本轮模块、框架（`target.framework`）、UI 库、是否 OpenSpec / Playwright / 设计规范等，列出：
   - **必用**（本轮开始前必须 `Read` SKILL.md）
   - **按需**（触发条件出现时再读）
   - **不适用**（一句话原因，避免误用）
3. 写入 `site-rewrite/indexes/skills-planned.yaml`（覆盖或按 `roundId` append）。  
4. 对「必用」项立即 `Read` 对应 `SKILL.md` 并按其执行；不得只列名不读。  
5. 典型常量表（按实际存在勾选，非强制全用）：

| 场景 | 常见 skill |
| --- | --- |
| UI 库组件 API | 配置的 `skills.uiLibrary`（如 antd / ant-design） |
| 提案 / 实现 / 归档 | openspec-proposal-creation(-cn)、openspec-implementation、openspec-archiving |
| 需求澄清 | grill-with-docs、domain-modeling |
| 浏览器对照 | Playwright MCP；next-browser（若为 Next 调试） |
| 设计 / a11y | frontend-design、web-design-guidelines（若任务匹配） |
| 性能 | vercel-react-best-practices（若任务匹配） |

未完成本步不得进入第 6 步。

---

## 6. 确认本次的需求是否还有不明白的，如果不明白则 使用 /grill-with-doc 进行交互式提问，不要瞎猜测，瞎假设等，一切都要明确

- Skill：**`grill-with-docs`**（`/grill-with-doc` 同此）。
- 不明处必须 grill；**禁止**瞎猜 / 瞎假设。

---

## 7. 如果使用了 /grill-with-doc 提问，提问没问题后，归档。

- 按 grill-with-docs / domain-modeling 归档（ADR、术语、或 context 文件）。
- 未归档不得进入提案定稿。

---

## 8. 使用 /openspec-proposal-creation 或者 /openspec-proposal-creation-cn 进行提案，提案中需要要求 将前 5点 写入到 提案中，编码中也要有以上前5点的要求，另外提案中完成了一个模块，就要通过 /palywright mcp 进行将要重构的网站、参考的网站 记性对比，最起码要匹配95%，才能继续下一模块，如果不足95%，则继续对这一模块进行调整，匹配95%后，则对这一模块进行提交，提交的commit要使用中文，然后在继续下一模块

- 按 `skills.proposal` 选择 cn / en OpenSpec 提案 skill。
- **提案与 tasks 必须写入第 1–5 点**（含「分析并启用相关 skills」）；`tasks.json` **第 0 项**为门禁。
- **模块规则**：实现后 Playwright 对比 legacy + reference + rewrite；`score >= matchThreshold`（默认 **0.95**）→ **中文 commit** → 下一模块；否则继续改本模块。
- 评分**必须**按 [match-rubric.md](match-rubric.md) 覆盖结构项与视觉项（字体、背景、边距、大小、边框、圆角、阴影、主色、图标图、hover、激活态、角标、动效等；无则 N/A）；结果写入 `site-rewrite/matches/` 并更新 `indexes/modules.yaml`。
- 等待用户批准提案后再进入第 9 步。

---

## 9. 提案没问题进行 /openspec-implementation 开发，按顺序完成任务

- 调用 **`openspec-implementation`**（或配置项）。
- 按 tasks 顺序；每模块：实现 → 对比 ≥95%（含视觉细则）→ 中文 commit → 下一模块。
- 未批准提案 → 不得编码。

---

## 10. 将本次重构的过程进行文档归档 重构的坑写进指定的文件

- 过程：`site-rewrite/playbooks/`（如 `<module>-rewrite.md`）。
- 踩坑：`site-rewrite/playbooks/pitfalls.md`（或配置 `docs.pitfallsFile`）。
- 按需 `openspec-archiving`。
- 归档正文不得含密钥。

---

## 依赖关系

```
f-site-rewrite-init → site-rewrite/
        ↓
1 Playwright → 2 源码+索引 → 3 playbooks/坑
        ↓
4 UI 库门禁 → 5 分析 skills
        ↓
6–7 grill + 归档
        ↓
8 OpenSpec 提案 → 9 implementation → 10 文档归档
```

## Commit

- 中文 message（`quality.commitLanguage: zh`）。
- 仅 `target.appRoot` 所属 git 提交应用代码；`site-rewrite/` 是否同仓提交遵循仓库惯例，**永不提交 secrets**。

## Stop conditions

| 条件 | 动作 |
| --- | --- |
| 无配置 | 跑 `f-site-rewrite-init` |
| 需求不明 | `grill-with-docs` |
| UI 不够用 | 停问；未同意则停止 |
| 未分析 skills | 不得 grill / 提案 |
| 匹配 < 95% | 不进入下一模块 |
| 未批准提案 | 不 implementation |
| 用户显式跳过某步 | 仅跳过该步并记录 |

## Additional resources

- [observation-template.md](observation-template.md)
- [match-rubric.md](match-rubric.md)
- Init：`../f-site-rewrite-init/`
- 索引约定：`../f-site-rewrite-init/indexes.md`
