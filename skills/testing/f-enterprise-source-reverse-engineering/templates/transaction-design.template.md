# 事务设计

| Transaction ID | Entry | Begin/Wrapper | Writes | Locks/Isolation | Commit/Rollback | External calls | Evidence |
|---|---|---|---|---|---|---|---|
| `${tx_id}` | `${entry}` | `${boundary}` | `${writes}` | `${locks}` | `${outcome}` | `${external}` | `${evidence}` |

## 填写说明
事务入口、结束和异常路径分别引用源码；外部调用是否位于事务内必须明确；未发现事务先写检查范围和 UNRESOLVED。只有完整人工复核后才能写 NOT_APPLICABLE，并在 API 索引加入 transaction_absence 与 reviewed_negative_evidence。
