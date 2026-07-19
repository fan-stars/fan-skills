---
name: sync-skills-catalog
description: 将 .agents/skills 按 skills-catalog.json 全量同步到分类化 skills/，并基于 AI 生成的中文说明渲染 README。用于更新、重建目录库；本 skill 不进入 skills-catalog，也不复制到 skills/。
---

# 同步 Skills 分类目录

本 skill 是本仓库的**运维工具**，不属于对外拷贝的目录库内容。

## 何时使用

- 新增/更新 `.agents/skills` 之后，需要重建 `skills/`
- 修改了 `skills-catalog.json`（分类映射）之后
- 用户要求「同步 skills」「更新分类目录」「重建 README」
- 需要为 skill 生成或刷新中文简介与详细介绍

## 约定（勿违反）

1. **真相源**：`.agents/skills/` + `skills-lock.json`
2. **分类元数据**：`skills-catalog.json`（**不含**中文文案字段）
3. **AI 说明缓存**：`generated/skill-docs.json`（由本流程生成/更新）
4. **派生产物**：根目录 `skills/` —— **禁止手改**；每次 `render` 先清空再重建
5. **本 skill** 位于 `.cursor/skills/sync-skills-catalog/`，**不得**写入 `skills-catalog.json`，**不得**复制到 `skills/`
6. **第一期不做 presets**

## 全流程（先生成，再渲染）

按顺序执行：

### 1. （可选）按 lock 更新 `.agents/skills`

```bash
npx skills update -y
```

若只改了 catalog、未改上游 skill，可跳过本步。

### 2. 查看哪些 skill 需要 AI 生成说明

在仓库根目录：

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status
```

- 输出 `NEED_GENERATE` 列表与哈希报告（`generated/status.json`）
- 源内容哈希未变且校验通过的条目可复用，不必重写

### 3. 为 NEED_GENERATE 列表生成/更新说明

对列表中**每一个** skill：

1. 阅读 `.agents/skills/<name>/SKILL.md`（必要时再读其引用的本地文档）
2. 按 [`docs/GENERATION_PROTOCOL.md`](docs/GENERATION_PROTOCOL.md) 写齐字段：
   `summary`、`capabilities`、`scenarios`、`coverage`、`notes`、`contentHash`
3. 将结果写入 `generated/skill-docs.json` 的 `skills.<name>`
4. **禁止**把中文说明写回 `skills-catalog.json`
5. `contentHash` 必须等于 `status.json` 中该 skill 的当前哈希

质量不达标时 `render`/`validate` 会失败。

### 4. 渲染分类目录

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render
```

脚本会：

- 校验 catalog 与 `.agents/skills` 一致，且无 `descriptionZh` 等文案字段
- 校验全部 skill 的 AI 说明存在且通过质量规则
- 清空 `skills/` 后按多分类映射复制完整副本
- 生成根与各分类 `README.md`：**总览表** + **逐 skill 详细介绍**

### 5. 校验

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

确认输出 `VALIDATE_OK`。

### 6. 抽查产物

- 多分类 skill（如 `frontend-design`）是否出现在多个目录且内容一致
- `f-java-springboot` 的 skills.sh 为「暂无」，GitHub 为本仓库链接
- 分类 README 同时有总览表与 `### \`name\`` 详细节
- `.cursor/skills/sync-skills-catalog` **未**出现在 `skills/` 下

## 相关文件

- `skills-catalog.json` — 分类映射（无中文文案）
- `skills-lock.json` — 上游安装锁
- `docs/GENERATION_PROTOCOL.md` — AI 说明结构与质量标准
- `generated/skill-docs.json` — AI 说明缓存
- `scripts/sync.py` — `status` / `render` / `validate`
