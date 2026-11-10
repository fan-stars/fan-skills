# skills-sync-journal

跨机器可移植的同步流水账。路径相对 `fan-skills` 库根；**禁止**写入机器绝对路径。

## 字段

| 字段 | 说明 |
| --- | --- |
| `id` | 稳定唯一 id（建议时间戳 + action + skill） |
| `action` | `sync-out` 或 `promote` |
| `skill` | skill 目录名 |
| `source_target` | promote 时的逻辑来源名（如 `cursor`） |
| `dest_targets` | sync-out 成功写入的逻辑 target 列表 |
| `library_rel` | 相对库根，如 `.agents/skills/f-skills-audit` |
| `contentHash` | 见 `f-skills-audit/reference.md` |
| `at` | ISO8601 时间 |
| `machine` | 主机名字符串（非路径） |
| `mode` | 通常 `copy`；跨机 apply 忽略 symlink |
| `note` | 可选说明 |

## 伴生规则（A1）

`promote` 成功后必须再追加一条同 skill 的 `action: sync-out`。  
`apply` 只处理 `sync-out`；仅有 `promote` 时不向全局写入。

## 示例（sync-out）

```yaml
id: 2026-11-10T120000Z-sync-out-f-skills-audit
action: sync-out
skill: f-skills-audit
dest_targets: [cursor]
library_rel: .agents/skills/f-skills-audit
contentHash: "replace-with-hex"
at: "2026-11-10T12:00:00+00:00"
machine: example-host
mode: copy
note: ""
```
