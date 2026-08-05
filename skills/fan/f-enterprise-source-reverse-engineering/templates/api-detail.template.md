# `${method} ${path}`

- API ID: `${api_id}`
- Route name: `${route_name}`
- Path/Query/Body/Header: `${parameters}`
- Authentication/Permission/Middleware: `${security}`
- Validation/Response/Error codes: `${contract}`
- Tables read/written: `${tables}`
- Transaction/Cache/Events/Jobs/External calls: `${side_effects}`
- Idempotency/Concurrency: `${concurrency}`

## Source evidence
| Stage | File | Symbol | Lines | SHA-256 | Classification |
|---|---|---|---|---|---|
| Route | `${route_file}` | route declaration | `${route_start}-${route_end}` | `${route_sha256}` | FACT |
| Entry | `${entry_file}` | `${entry_symbol}` | `${entry_start}-${entry_end}` | `${entry_sha256}` | FACT |

## 填写说明
至少覆盖路由、入口、验证、核心 Service、持久化、事务、异步/外部和响应；缺失阶段写 UNRESOLVED，不能删行规避。
