---
name: sync-skills-catalog
description: 将 .agents/skills 按 skills-catalog.json 全量同步到分类化 skills/，并生成中文 README。用于更新、重建目录库；本 skill 不进入 skills-catalog，也不复制到 skills/。
---

# 同步 Skills 分类目录

本 skill 是本仓库的**运维工具**，不属于对外拷贝的目录库内容。

## 何时使用

- 新增/更新 `.agents/skills` 之后，需要重建 `skills/`
- 修改了 `skills-catalog.json`（分类或中文简介）之后
- 用户要求「同步 skills」「更新分类目录」「重建 README」

## 约定（勿违反）

1. **真相源**：`.agents/skills/` + `skills-lock.json`
2. **派生产物**：根目录 `skills/` —— **禁止手改**；每次同步先清空再重建
3. **本 skill** 位于 `.cursor/skills/sync-skills-catalog/`，**不得**写入 `skills-catalog.json`，**不得**复制到 `skills/`
4. **第一期不做 presets**

## 全流程

按顺序执行：

### 1. （可选）按 lock 更新 `.agents/skills`

```bash
npx skills update -y
```

若只改了 catalog、未改上游 skill，可跳过本步。

### 2. 运行同步脚本

在仓库根目录：

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py
```

脚本会：

- 校验 catalog 与 `.agents/skills` 一致
- 清空 `skills/`
- 按多分类映射复制 skill 完整副本
- 生成 `skills/README.md` 与各分类 `README.md`（中文；含名称、路径、简介、skills.sh、GitHub；缺失 skills.sh 显示「暂无」）

### 3. 检查产物

- 抽查多分类 skill（如 `frontend-design`）是否出现在多个目录且内容一致
- 抽查 `f-java-springboot` 的 skills.sh 为「暂无」，GitHub 为本仓库链接
- 确认 `.cursor/skills/sync-skills-catalog` **未**出现在 `skills/` 下

## 相关文件

- `skills-catalog.json` — 分类映射与中文简介
- `skills-lock.json` — 上游安装锁
- `.cursor/skills/sync-skills-catalog/scripts/sync.py` — 同步实现
