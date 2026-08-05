# 业务流程 `${process_id}`

| 步骤 | 入口/动作 | 条件 | 数据更新 | 异步/外部副作用 | 失败补偿 | Evidence |
|---:|---|---|---|---|---|---|
| 1 | `${action}` | `${condition}` | `${writes}` | `${side_effect}` | `${recovery}` | `${evidence}` |

## 填写说明
步骤按真实执行顺序；条件、更新和补偿分别引用证据；跨事务或异步边界必须显式标出，推断步骤标 INFERENCE。
