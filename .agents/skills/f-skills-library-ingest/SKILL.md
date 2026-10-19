---
name: f-skills-library-ingest
description: >-
  Use when consolidating Agent Skills from global agent homes and project trees
  into a categorized skills library (catalog + .agents/skills), refreshing an
  existing skills directory library, or the user mentions 整理 skills、入库、
  skills catalog ingest、盘点 cursor/codex skills.
---

# f-skills-library-ingest

把散落在各 Agent 全局目录与项目里的 skills，**有选择地**纳入一个「目录库」仓（真相源 `.agents/skills/` + `skills-catalog.json`），再交给库内同步流程生成分类浏览树。

**核心原则：** 先盘点与确认范围/分类，再拷贝；分类树是派生产物，禁止手改。

## 何时使用

- 新建或扩充 skills 目录库（如 `fan-skills` 形态）
- 全局 `~/.cursor/skills`、`~/.codex/skills` 等与库内真相源不一致
- 需要按分类整理、迁移旧/新 OpenSpec 套件、附带 slash commands
- 用户说「整理 skills / 入库 / 同步目录库 / catalog ingest」

## 何时不用

- 只需重建已有真相源的分类副本 → 用库内 `sync-skills-catalog`
- 只切换 legacy/opsx 投影 → 用 `f-openspec-profile-switch`
- 只盘点 Git 仓来源 → 用 `f-git-origin-doc`

## 前置约定（目标库必须满足）

目标仓根（下称 `$LIB`）应具备：

| 路径 | 角色 |
| --- | --- |
| `.agents/skills/<name>/` | 真相源 |
| `skills-catalog.json` | 分类映射（无中文文案字段） |
| `skills/` | 派生产物（禁止手改） |
| 同步入口 | 通常 `.cursor/skills/sync-skills-catalog/scripts/sync.py` |

若缺 catalog/sync，先搭齐再入库，或只完成盘点报告不写盘。

可选：`commands/`（与 opsx/superpowers 配套的 canonical 嵌套命令树）。布局见 [reference.md](reference.md)。

## 流程

```text
- [ ] 1. 解析 $LIB 与扫描根（可覆盖，勿写死单机路径）
- [ ] 2. 盘点候选 skills（名 → 来源路径列表）
- [ ] 3. 与 $LIB/.agents/skills 做差集；排除默认黑名单
- [ ] 4. 与用户确认：纳入清单、排除项、分类映射、是否含 commands
- [ ] 5. 拷贝到 .agents/skills（完整目录）；更新 skills-catalog.json
- [ ] 6. （可选）写入/占位 commands/
- [ ] 7. 按库内 sync-skills-catalog：status → 生成说明 → render → validate
- [ ] 8. 更新 $LIB/README 分类一览；汇报；勿擅自 push
```

确认前**不要**拷贝或改 catalog。用户沉默 ≠ 同意。

### 1. 解析路径

- `$LIB`：用户指定，或含 `skills-catalog.json` + `.agents/skills` 的当前工作区根
- 扫描根：默认列表见 [reference.md](reference.md)；用户可增删
- 所有路径用 POSIX；脚本可移植，禁止把某一台机器的绝对路径写进 skill 正文当唯一来源

### 2. 盘点

对每个扫描根，收集**直接子目录**且含 `SKILL.md` 的名字。

记录：`name → [{root, path}]`（同名多来源时保留优先级：见 reference「来源优先级」）。

### 3. 差集与黑名单

- **已在库内**：默认跳过（除非用户要求覆盖/升级）
- **默认排除**：Cursor 产品内置目录（如 `~/.cursor/skills-cursor`）、明显第三方示例 skill、用户点名排除项
- **依赖树内** `.agents/skills`（`node_modules`/`vendor` 下）忽略

### 4. 分类

- 沿用 `$LIB/skills-catalog.json` 已有 `categories` 键；新分类须先写入 `categories` 再引用
- 嵌套分类用 `/`（如 `opsx/openspec`、`web/react`）
- 同一 skill 可多 `categories`（多目录副本由 sync 生成）
- OpenSpec **旧套**与 **opsx 新套**、**superpowers** 必须分开放；不要塞进同一个 `spec` 糊成一团
- 本地 Fan/`f-*` 技能：`fan`（可兼技术分类）；**禁止**伪造 `githubUrl`/`skillsShUrl`

分类启发式与命令树约定见 [reference.md](reference.md)。

### 5. 写入真相源

```bash
# 示例：从选定来源完整拷贝（覆盖前先确认）
rm -rf "$LIB/.agents/skills/<name>"
cp -a "<source>/<name>" "$LIB/.agents/skills/<name>"
```

然后更新 `skills-catalog.json`：

- `skills` 键集合必须与 `.agents/skills` 目录集合一致
- 条目不得含 `descriptionZh` / `detailsZh`
- 每个 skill 至少一个合法 `categories[]`

### 6. Commands（可选）

若用户要求「命令一起进仓」：

- 规范形态：`$LIB/commands/<ns>/<id>.md`（嵌套，非扁平）
- `ns` 常见：`opsx`、`superpowers`；`id` 为 skill 名去掉前缀后的段
- 来源空则写 **PLACEHOLDER** 短文件（模板见 reference），以对应 skill 为准
- commands **不**进入 `skills-catalog.json`，**不**经 sync 复制到 `skills/`

### 7. 同步派生产物

严格按目标库的 `sync-skills-catalog`（或等价文档）执行：`status` → 为 `NEED_GENERATE` 写中文说明 → `render` → `validate`。

- 中文说明写入库约定的 `generated/skill-docs.json`（或文档指定路径）
- **禁止**手改 `skills/` 下文件来「修分类」
- `VALIDATE_OK` 前不得宣称完成

### 8. 汇报

列出：扫描根、纳入/跳过/排除数量、新分类、commands 是否占位、validate 结果、未 push。提醒：分发到其他机器 = 拉取 `$LIB` 后按需把需要的 skill 拷到该机全局 skills 目录。

## 不要做

- 不经确认批量覆盖已有真相源
- 手改 `skills/` 派生产物
- 把 `skills-cursor` 等产品内置 skill 当库内容入库
- 为本地 skill 编造上游 URL
- 默认改无关项目的 `.gitignore` / 乱 commit / 擅自 push
- 把本 skill 与某次单机路径、单次会话叙事绑死

## 常见错误

| 错误 | 纠正 |
| --- | --- |
| 直接改 `skills/web/...` | 改 `.agents/skills` + catalog，再 sync |
| 旧 OpenSpec 与 `/opsx:*` 混在同一分类 | 拆 `openspec-legacy` 与 `opsx/openspec`（或库内等价名） |
| catalog 与 `.agents/skills` 集合不一致 | sync 会失败；先对齐再 render |
| 说明字段过短或无汉字 | 按 GENERATION_PROTOCOL 补齐后再 render |
| 只在本机 `~/.cursor/skills` 改、不入库 | 其他机器无法复现；以 `$LIB` 为分发源 |

## 相关

- 库内渲染：目标库的 `sync-skills-catalog`
- OpenSpec 双套投影：`f-openspec-profile-switch`
- 详细约定与模板：[reference.md](reference.md)
