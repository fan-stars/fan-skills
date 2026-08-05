# API 设计

| API ID | Method | Path | Auth/Permission | Validation | Read tables | Write tables | Transaction | Idempotency | Detail |
|---|---|---|---|---|---|---|---|---|---|
| `${api_id}` | `${method}` | `${path}` | `${auth}` | `${validator}` | `${reads}` | `${writes}` | `${transaction}` | `${idempotency}` | `${detail_file}` |

## 填写说明
每个已发现接口必须有独立 detail；Method/Path 来自路由，权限和事务来自实际实现；未发现不能填写“默认有”。
