---
name: f-skills-apply
description: >
  Use when replaying portable skills-sync-journal sync-out entries onto
  this machine's global skill targets after git pull. 跨机 apply、回放 journal。
---

# f-skills-apply

只回放未在本机应用的 **`sync-out`** journal；用库现行内容 **copy** 到逻辑 target（S1）。本机状态：`$HOME/.config/fan-skills/applied.json`。契约：[../f-skills-audit/reference.md](../f-skills-audit/reference.md)。

## 规则

- 跳过已应用 id；`--force` 可重放
- `promote` 条目不写全局（需伴生 sync-out）
- 目标分歧仍走确认（或 `--yes`）

## 命令

```bash
python3 .agents/skills/f-skills-audit/scripts/cli.py apply --library .
python3 .agents/skills/f-skills-audit/scripts/cli.py apply --library . --yes
```
