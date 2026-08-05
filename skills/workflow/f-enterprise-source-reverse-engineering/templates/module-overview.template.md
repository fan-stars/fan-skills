# 模块概览

## 职责与边界
- Classification: `${classification}`
- Responsibility: `${responsibility}`
- Included: `${included}`
- Excluded: `${excluded}`
- Aliases: `${aliases}`
- Upstream/Downstream: `${dependencies}`
- Boundary confidence: `${confidence}`

## 候选文件
| 文件 | 分数 | 归属角色 | 纳入信号 | 证据 |
|---|---:|---|---|---|
| `${file}` | `${score}` | PRIMARY | `${route/table/call}` | `${evidence}` |

## 填写说明
职责必须来自调用链和表操作；文件名只可作为低分信号；边界不明确时保持 UNRESOLVED/LOW。
