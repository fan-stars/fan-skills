# 模块比较 `${module}`

| Dimension | Project A | A source IDs | Project B | B source IDs | Requirement IDs | Difference/Conflict |
|---|---|---|---|---|---|---|
| `${dimension}` | `${a_finding}` | `${a_ids}` | `${b_finding}` | `${b_ids}` | `${req_ids}` | `${difference}` |

## 前置检查
- A/B status: `${a_status}` / `${b_status}`
- Stale evidence: `${stale_status}`
- Boundary aligned: `${boundary_aligned}`

## 填写说明
每个结论同时保留 A/B 来源 ID；前置检查不通过只填写阻塞项，不生成候选决策。
