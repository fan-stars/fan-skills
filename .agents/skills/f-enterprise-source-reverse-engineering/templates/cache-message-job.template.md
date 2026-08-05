# 缓存、消息与任务

| Type | Name/Key | Producer/Writer | Consumer/Reader | TTL/Schedule | Retry/Idempotency | Transaction relation | Evidence |
|---|---|---|---|---|---|---|---|
| `${type}` | `${name}` | `${producer}` | `${consumer}` | `${ttl_or_schedule}` | `${retry}` | `${transaction}` | `${evidence}` |

## 填写说明
缓存填写读、写、失效和 TTL；消息填写 payload、生产者、消费者和重试；Job 填调度周期及重复执行保护。
