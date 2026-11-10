---
name: f-skills-promote
description: >
  Use when promoting a single edited global skill back into fan-skills
  .agents/skills, writing promote plus companion sync-out journals, then
  running sync-skills-catalog. 回写入库、promote。
---

# f-skills-promote

将**已知单个** skill 从逻辑 target 拷回真相源，写 `promote` journal，并**必须**再写伴生 `sync-out` journal（A1）。契约：[../f-skills-audit/reference.md](../f-skills-audit/reference.md)。

## 何时不用

- 批量扫描多根、挑选入库 → `f-skills-library-ingest`
- 只对比 → `f-skills-audit`
- 只从库推到全局 → `f-skills-sync-out`

## 命令

```bash
python3 .agents/skills/f-skills-audit/scripts/cli.py promote --library . --skill NAME --from cursor --yes
```

成功后必须继续：`sync-skills-catalog` 的 status → 生成说明 → render → validate。**禁止手改** `skills/` 派生产物。
