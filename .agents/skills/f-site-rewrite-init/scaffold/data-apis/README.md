# 数据接口调用记录

每次对 `dataApis` 发起（或从浏览器/代理观察到）请求后，在此目录新增或更新一条记录，并同步 `indexes/data-api-calls.yaml`。

- **可提交**：URL 形态、query/body 字段名与示例值（脱敏）、响应字段结构与样例（脱敏）
- **禁止**：Authorization、Cookie、token、密码、个人隐私字段明文

模板见 `.agents/skills/f-site-rewrite-init/data-api-record-template.md`。

命名建议：`<apiId>-<method>-<path-slug>-<YYYYMMDD>.md`
