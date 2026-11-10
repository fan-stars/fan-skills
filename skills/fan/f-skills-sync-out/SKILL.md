---
name: f-skills-sync-out
description: >
  Use when pushing selected fan-skills from the library truth source to
  global AI skill directories (agents/cursor/codex) using skills-sync profiles.
  外推、同步到全局 skills。
---

# f-skills-sync-out

按 `skills-sync.yaml` 的 profile 将真相源 skill **copy** 到可写逻辑 target。契约：[../f-skills-audit/reference.md](../f-skills-audit/reference.md)。

## 规则

- 仅 profile ∩ ¬exclude；未选中的不写
- 指纹相同跳过；不同须确认（或 `--yes`）
- 成功后写可移植 `sync-out` journal
- 禁止写入 `skills-cursor` / `.system`；默认不推 `sync-skills-catalog`

## 命令

```bash
python3 .agents/skills/f-skills-audit/scripts/cli.py sync-out --library . --profile default
python3 .agents/skills/f-skills-audit/scripts/cli.py sync-out --library . --profile default --skill f-skills-audit --yes
```
