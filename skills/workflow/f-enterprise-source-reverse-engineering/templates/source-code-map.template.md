# 源码地图

| 序号 | 层次 | 文件 | 符号 | 行范围 | SHA-256 | Classification |
|---:|---|---|---|---|---|---|
| 1 | Route | `${file}` | `${symbol}` | `${start}-${end}` | `${sha256}` | FACT |

## Full call chain
`${route}` → `${middleware}` → `${controller}` → `${validator}` → `${service}` → `${repository}` → `${async_or_external}` → `${response}`

## 填写说明
每个节点使用当前相对路径、符号、完整行范围和哈希；断点写 UNRESOLVED，静态推断调用写 INFERENCE/MEDIUM。
