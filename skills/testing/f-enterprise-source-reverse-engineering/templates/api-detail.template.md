# `${method} ${path}`

- API ID: `${api_id}`
- Route name: `${route_name}`
- Path/Query/Body/Header: `${parameters}`
- Authentication/Permission/Middleware: `${security}`
- Validation/Response/Error codes: `${contract}`
- Tables read/written: `${tables}`
- Transaction/Cache/Events/Jobs/External calls: `${side_effects}`
- Idempotency/Concurrency: `${concurrency}`

## Coverage
| Dimension | Status | Rationale | Evidence type |
|---|---|---|---|
| Validation | PRESENT/UNRESOLVED/NOT_APPLICABLE | `${validation_rationale}` | validation / validation_absence |
| Service | PRESENT/UNRESOLVED/NOT_APPLICABLE | `${service_rationale}` | service / service_absence |
| Persistence/Tables | PRESENT/UNRESOLVED/NOT_APPLICABLE | `${persistence_rationale}` | persistence / persistence_absence |
| Transaction | PRESENT/UNRESOLVED/NOT_APPLICABLE | `${transaction_rationale}` | transaction / transaction_absence |
| Side effect | PRESENT/UNRESOLVED/NOT_APPLICABLE | `${side_effect_rationale}` | side_effect / side_effect_absence |

## Source evidence
| Stage | File | Symbol | Lines | SHA-256 | Classification |
|---|---|---|---|---|---|
| Route | `${route_file}` | route declaration | `${route_start}-${route_end}` | `${route_sha256}` | FACT |
| Entry | `${entry_file}` | `${entry_symbol}` | `${entry_start}-${entry_end}` | `${entry_sha256}` | FACT |

## 填写说明
至少覆盖路由、入口、验证、核心 Service、持久化、事务、异步/外部和响应；缺失阶段写 UNRESOLVED，不能删行规避。NOT_APPLICABLE 只能通过 `record_reviewed_absence.py` 写入，并引用带 reviewer、reviewed_at、当前哈希和 `semantic_basis=reviewed_negative_evidence` 的对应 absence 证据。
