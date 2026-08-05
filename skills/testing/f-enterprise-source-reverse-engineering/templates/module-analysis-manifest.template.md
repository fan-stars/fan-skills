# 模块分析清单

- Project: `${project}`
- Module: `${module}`
- Run: `${analysis_run_id}`
- Repository commit: `${commit}`
- Source index version: `${index_version}`
- Status: `PARTIAL`
- Boundary confidence: `MEDIUM`

## Scope
包含：`${included_scope}`；排除：`${excluded_scope}`；上游：`${upstream}`；下游：`${downstream}`。

## Evidence ledger
| ID | Classification | Evidence | Confidence |
|---|---|---|---|
| `${id}` | FACT | `${file}:${start}-${end}` SHA `${sha256}` | HIGH |

## 填写说明
Project、commit、索引版本必须来自本次运行；Status 只有通过全部门禁才改为 ANALYZED；Evidence 必须引用当前文件哈希和完整逻辑范围。
