# Commands（opsx 配套）

本目录存放与 `opsx/openspec`、`opsx/superpowers` 技能对应的 slash 命令，布局对齐
`~/.openspec-profiles/opsx/commands/` 的 **嵌套规范**：

- `opsx/<id>.md` → 用户输入 `/opsx:<id>`（Cursor 投影时常变为扁平 `opsx-<id>.md`）
- `superpowers/<id>.md` → `/superpowers:<id>`

本仓只保存 **canonical 嵌套** 形态。部署到各工具由 `f-openspec-profile-switch` 负责整形。

若文件正文含 `PLACEHOLDER`，表示收录时本机 vault 命令为空，应以 skill 为准，并用
`openspec update` / profile-switch 再生后覆盖。
