# f-base-codegen-mcp 缺口

记录日期 2026-11-15。这里只记问题，不改 `SKILL.md`、`reference.md` 和 `scripts/apply_bundle.py` 的行为。远程模板的对应条目在 MCP 工作区 `docs/standards/codegen-gaps.md`。

1. `reference.md` 把 `codegen_import` 的 `dataSourceConfigId` 写成可选。服务端可能拒绝缺少该字段的请求。技能说明和服务端本次都不改。
2. 菜单和按钮 id 以本地 SQL 规范为准，由人对照本地 SQL 补全。父级 INSERT 已存在就用那条 id；不存在则按号段取号。按钮同样对照已有 INSERT。远程 MCP 看不到本地 SQL，不要把「脚本自动发号」写成已经可靠。
3. `sql/mysql/README.md` 的删表条数、表张数、菜单下一个由人维护。脚本不改这些计数。
4. 前端文件按 bundle 落盘，本次不加「不写前端」开关。
5. 空的 Mapper XML 要保留。脚本只是照 manifest 复制；远程会带上这个空文件。不要改成跳过空 XML。