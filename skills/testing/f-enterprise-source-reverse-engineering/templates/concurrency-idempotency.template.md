# 并发与幂等

| Scenario | Competing operations | Idempotency key | Lock/Constraint | State guard | Failure/Retry | Risk | Evidence |
|---|---|---|---|---|---|---|---|
| `${scenario}` | `${operations}` | `${key}` | `${protection}` | `${guard}` | `${failure}` | `${risk}` | `${evidence}` |

## 填写说明
把已实现保护与建议分开；没有锁、唯一键或状态条件证据时 protection 填 `NOT_FOUND` 并登记 RISK。
