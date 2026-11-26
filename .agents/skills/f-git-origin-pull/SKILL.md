---
name: f-git-origin-pull
description: >-
  Use when cloning or fetching independent Git repos listed in
  .git-origin/README.md, restoring workspace repos on a new machine, or
  syncing remotes from that manifest. Do not use to regenerate the manifest
  (use f-git-origin-doc).
---

# f-git-origin-pull

按文档机器块恢复/更新独立 Git 工作树。解析规则与字段见同伴契约：

[f-git-origin-doc/reference.md](../f-git-origin-doc/reference.md)

## 何时使用

- 用户要求按 `.git-origin` / 远程文档拉取、克隆、同步子仓远程
- 在新机器上按已有文档恢复工作区仓
- **不要**用本技能重新生成或改写清单（用 `f-git-origin-doc`）

## 硬约束

- 只 `git fetch` / `git clone` / `git remote add`（及用户确认后的 `set-url`）
- **禁止** `merge`、`rebase`、`pull`（除非用户另行明确要求）
- **禁止**按文档 `branch` 执行 checkout
- **禁止**创建或修改 `symlinks[]`
- remote **名已存在但 URL 与文档不同**：立即停止该仓后续操作，列出冲突，请用户确认后再继续

## 流程

```text
- [ ] 定位工作区根与 .git-origin/README.md
- [ ] 提取并解析 git-origin-manifest YAML
- [ ] 确定目标子集（默认全部 repos[]；用户点名则过滤）
- [ ] 仅对 selected 逐个处理 repos[]
- [ ] 跳过 symlinks[]（仅汇报；outside_ancestor 标非祖仓）
- [ ] 汇报 selected / not_in_scope / 成功 / 跳过 / 待确认项
```

### 1. 解析机器块

读取 `.git-origin/README.md`，提取：

```text
<!-- git-origin-manifest:start -->
```yaml
...
```
<!-- git-origin-manifest:end -->
```

`version` 必须为 `1`；否则停止并说明需先用 `f-git-origin-doc` 重新生成。

旧文档若含**绝对路径**的 `ancestor.path`：**不阻断**拉取；可提示用户稍后运行 `f-git-origin-doc` 将路径相对化。拉取逻辑只依赖 `repos[]` / `symlinks[]`，不以祖先路径做 clone 目标。

### 2. 确定目标子集（GORI-C-011 / C-012）

- **默认**：目标 = 机器块全部 `repos[]`（GORI-C-011）。
- **用户点名**：仅当 `repos[].path` **全等**或 `repos[].purpose` **全等**时纳入 `selected`；禁止末段/子串「合理对应」等猜测性匹配。
- **点名无精确匹配**：将该点名列入报告为未匹配；**不得**猜测 path 去 clone。若同轮另有已精确匹配的条目，仍只处理那些匹配项。
- 汇报区分：
  - `selected`：纳入本次 clone/fetch 的 path
  - `not_in_scope`：文档有、用户未点名（本机缺失也不 clone）
  - 未匹配的点名：单独列出，不进入 `selected`

### 3. 处理每个 selected repo

`dir = <工作区根>/<repos[].path>`。未选中的条目跳过，记入 `not_in_scope`。

#### 3.1 目录不存在

1. 选 clone URL：`remotes` 中 `name == origin` 的 url；若无 `origin`，用 **列表第一个** remote 的 url  
2. `git clone <url> <dir>`  
3. 对尚未存在的其余 remote：`git -C <dir> remote add <name> <url>` 然后 `git -C <dir> fetch <name>`  
4. 若 clone 所用 remote 名不是文档中的名（极少见），按文档把远程名调整到一致（`remote rename` / `add`），保证文档中每个 name 都存在且 URL 一致后再 fetch

#### 3.2 目录存在

1. 确认 `<dir>` 是 Git 工作树；否则停止该条目并报告  
2. 对文档中每个 remote：
   - 本地无该名：`git remote add <name> <url>` → `git fetch <name>`
   - 本地有该名且 URL 相同（比较 fetch URL）：`git fetch <name>`
   - 本地有该名但 URL 不同：**停止**，输出文档 URL vs 本地 URL，等待用户确认（确认改 URL 后再 `set-url` + `fetch`；确认保留本地则跳过该 remote）

### 4. 软连接（GORI-C-013 / C-014）

对 `symlinks[]`：**永不创建**、不删除、不改 target。

汇报每条：

- `path` 与 `target`
- 需人工确保（本机是否已存在由用户处理）
- 若 `outside_ancestor` 为 `true`：明确标注 **非祖仓、拉取不创建、需人工确保，勿盲建**（字段缺省视为 `false`，不必按非祖仓标注）

### 5. 汇报

按仓列出：`selected` / `not_in_scope` / cloned / fetched remotes / skipped / awaiting-confirmation；软连接列出 path/target/`outside_ancestor` 与人工确保提示。勿声称已合并或已切换分支。
