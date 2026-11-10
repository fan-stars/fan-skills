---
name: f-skills-audit
description: >
  Use when comparing fan-skills truth (.agents/skills) to global AI skill
  roots, reviewing drift before sync-out/promote, or checking portable
  skills-sync config. 盘点、对比、skills 同步审计。
---

# f-skills-audit

只读盘点库真相源与各逻辑 target。契约见 [reference.md](reference.md)。

## 何时不用

- 要推到全局 → `f-skills-sync-out`
- 单 skill 回写库 → `f-skills-promote`
- 批量入库 → `f-skills-library-ingest`
- 按 journal 跨机对齐 → `f-skills-apply`

## 命令

在 `fan-skills` 库根：

```bash
python3 .agents/skills/f-skills-audit/scripts/cli.py validate-config --library .
python3 .agents/skills/f-skills-audit/scripts/cli.py audit --library . -v
```

本流程**不修改**任何 skill 目录。硬排除：永不把 `~/.cursor/skills-cursor` 当可写目标；不改 `.system`。`cursor-store` 可探测则只读对比。
