# 数据接口调用记录模板

复制到 `site-rewrite/data-apis/<apiId>-<method>-<path-slug>-<YYYYMMDD>.md`。

```markdown
# Data API: <apiId> <METHOD> <path>

- datetime:
- apiId:                    # refactor.config.yaml → dataApis[].id
- env: test | prod | …
- method: GET | POST | …
- path:                     # 相对 pathPrefix
- pathPrefix:               # 如 /v33
- query:                    # 参数名与示例值（脱敏）；无则 —
- body:                     # JSON 字段说明；无则 —
- headersNoted: []          # 仅头名称，如 [Content-Type]；勿写 token 值
- httpStatus:
- contentType:
- moduleIds: []             # 关联重写模块
- source: capture | server-outbound | docs

## Request（形态）

\`\`\`
METHOD {baseUrl}{pathPrefix}/{path}?…
\`\`\`

| 参数 | 位置 | 类型 | 必填 | 示例（脱敏） | 说明 |
| --- | --- | --- | --- | --- | --- |
|  | query/body |  |  |  |  |

## Response（字段）

| 字段路径 | 类型 | 说明 | 示例（脱敏） |
| --- | --- | --- | --- |
|  |  |  |  |

## Response 样例（脱敏）

\`\`\`json
{}
\`\`\`

## Mapping notes

- 映射到访客 VO / mock 时注意：
- 易错语义（如 hidden）：

## Related

- sources-read:
- playbook:
```
