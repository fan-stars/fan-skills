# f-skills-library-ingest 参考

## 默认扫描根（可覆盖）

按存在性探测，**不要**假设都存在：

| 优先级 | 路径模式 | 说明 |
| --- | --- | --- |
| 1 | `$HOME/.openspec-profiles/opsx/skills` | opsx vault（若用 profile-switch） |
| 2 | `$HOME/.openspec-profiles/legacy/skills` | legacy vault |
| 3 | `$HOME/.cursor/skills` | Cursor 用户 skills |
| 4 | `$HOME/.codex/skills` | Codex |
| 5 | `$HOME/.agents/skills` | 通用 agents |
| 6 | `$HOME/.claude/skills` | Claude Code（若有） |
| 7 | `$HOME/.qoder/skills` | Qoder（若有） |
| — | 用户给出的项目根下 `.agents/skills`、`.cursor/skills` | 项目特有 |

**默认永不扫描为入库源：**

- `$HOME/.cursor/skills-cursor`（Cursor 产品内置）
- 任意 `node_modules` / `vendor` / `.pnpm` 下的嵌套 skills

同名多来源时：vault（openspec-profiles）> 用户全局 cursor/codex > 项目 `.agents/skills`。用户指定来源时以用户为准。

## 分类启发式（建议，非强制）

| 信号 | 建议 categories |
| --- | --- |
| 名匹配旧套 `openspec-archiving` / `openspec-proposal-creation*` / `openspec-context-loading` / `openspec-implementation` | `openspec-legacy`（或库内等价） |
| 名匹配新套 `openspec-explore` / `openspec-propose` / `openspec-*-change` 等 | `opsx/openspec` |
| `superpowers-*` | `opsx/superpowers` |
| `f-*` 团队自研 | `fan`（可兼 `java` / `web/react` 等） |
| `antd` / `ant-design` / `next` / `vercel-react-*` | `web/react` |
| `nuxt` / `vben` | `web/vue` |
| `frontend-design` / `finesse-*` / `frame-smith` / `web-design-guidelines` | `web/design` |
| `docx` / `pdf` / `pptx` / `xlsx` | `docs` |
| `java-springboot` / `graal` / native-image 相关 | `java` |
| `mcp-builder` | `mcp` |
| `webapp-testing` / `agent-browser` | `testing` |
| `grill*` / `domain-modeling` / `codebase-design` | `workflow` |
| `create-agentsmd` / `create-specification` | `spec`（通用规格，不是 OpenSpec 套件） |

库内若尚无某分类键，先往 `skills-catalog.json` → `categories` 增加 `title`/`description`，再引用。

## Commands 树

与 `f-openspec-profile-switch` vault 一致：**只存嵌套 canonical**。

```text
$LIB/commands/
  README.md
  opsx/<id>.md          # /opsx:<id>
  superpowers/<id>.md   # /superpowers:<id>
```

- OpenSpec 新套 skill `openspec-<id>` → `commands/opsx/<id>.md`
- Superpowers skill `superpowers-<id>` → `commands/superpowers/<id>.md`
- 部署到 Cursor 等工具时的扁平改名由 profile-switch 负责，本库不保存扁平副本

### PLACEHOLDER 模板

```markdown
---
name: ID
description: PLACEHOLDER — commands 源为空；待 openspec update 或 profile-switch 再生后替换。
---

# /NS:ID

占位命令。完整流程以 skill `SKILL`（`.agents/skills/SKILL`）为准。

再生后请用 vault 规范嵌套路径覆盖本文件，勿手写业务步骤。
```

将 `ID` / `NS` / `SKILL` 替换为实际值。

## 盘点用便携命令示例

```bash
# 列出某根下 skill 名
list_skills() {
  local root="$1"
  [ -d "$root" ] || return 0
  for d in "$root"/*/; do
    [ -f "${d}SKILL.md" ] || continue
    basename "$d"
  done | sort
}

# 差集：候选有、库内无
comm -23 <(list_skills "$SCAN_ROOT") <(list_skills "$LIB/.agents/skills")
```

## 入库后同步（目标库）

在 `$LIB`：

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status
# 为 NEED_GENERATE 填写 generated/skill-docs.json（协议见该 skill 的 docs）
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

其他机器：clone/pull `$LIB` 后，按需将 `.agents/skills/<name>` 拷到该机全局 skills 根即可，无需强制本机绝对路径。
