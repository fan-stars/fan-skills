# git-origin 文档契约（v1）

`f-git-origin-doc` 与 `f-git-origin-pull` 共同遵守本文。机器块是拉取权威数据源；人读部分不得与机器块冲突，冲突时以机器块为准。

## 文件位置

工作区根目录：`.git-origin/README.md`

## 机器块

必须且仅有一处，使用 HTML 注释包裹 + YAML fenced code：

```markdown
<!-- git-origin-manifest:start -->
```yaml
version: 1
inventoried_at: "YYYY-MM-DD"
workspace: "<工作区目录名>"
ancestor:
  path: ".."   # 相对工作区根；禁止绝对路径；无祖先则为 ""
  has_gitlink: false
repos:
  - path: "relative/dir"
    purpose: "短用途"
    branch: "master"
    remotes:
      - name: origin
        url: "git@example.com:org/repo.git"
symlinks:
  - path: "link-name"
    target: "../sibling-or-relative/target"
    outside_ancestor: false
```
<!-- git-origin-manifest:end -->
```

### 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `version` | 是 | 固定 `1` |
| `inventoried_at` | 是 | 盘点日 `YYYY-MM-DD` |
| `workspace` | 是 | 工作区根目录名 |
| `ancestor.path` | 是 | 相对工作区根的 POSIX 路径（如 `..`）；无则 `""`；**禁止绝对路径** |
| `ancestor.has_gitlink` | 是 | 祖先索引是否含本工作区 gitlink（`160000`） |
| `repos[].path` | 是 | 相对工作区根，POSIX，无尾斜杠 |
| `repos[].purpose` | 是 | 短用途；可用目录名，勿编造长业务文案 |
| `repos[].branch` | 是 | 盘点时当前分支名；**拉取时不 checkout** |
| `repos[].remotes` | 是 | **全部**远程；至少 1 项；顺序见「更新语义」合并规则 |
| `repos[].remotes[].name` | 是 | 远程名 |
| `repos[].remotes[].url` | 是 | fetch URL（与 push 不同时仍记 fetch） |
| `symlinks` | 是 | 无则 `[]` |
| `symlinks[].path` | 是 | 相对工作区根 |
| `symlinks[].target` | 是 | 相对工作区根的 POSIX 路径（由 `readlink` 结果换算）；**禁止绝对路径** |
| `symlinks[].outside_ancestor` | 否 | 规范化 target 落在祖先根之外（无祖先则落在工作区根之外）时为 `true`；缺省 / 旧文档缺失该字段视为 `false` |

路径可移植（GORI-C-001 / C-002 / C-003）：机器块与人读部分均不得写入本机绝对路径；`ancestor.path` 与 `symlinks[].target` 一律相对工作区根。

### 不写入 `repos` 的路径

依赖安装树内嵌套 `.git`（如 `vendor/`、`node_modules/` 下）**排除**，不写机器块、不当独立仓。

`reference/` 等容器本身不是 Git 时：不写特殊容器章节；其下独立 Git 目录照常进 `repos`。

## 更新语义

重新生成或更新 `.git-origin/README.md` 时：

1. **读旧 → 合并 → 写回**：先解析既有机器块，再与本机盘点合并，最后写回；禁止仅按本机盘点整表覆盖导致丢条目。
2. **仅文档有的条目默认保留**：旧机器块中有、本机不存在的 `repos[]` / `symlinks[]` 默认保留，并向用户报告 `kept_absent`（软连接可用 `kept_absent_symlink`）。
3. **删除闸门**：不得因本机缺失或「整表按本机重写更干净」等理由缩小清单。仅当用户**点名删除**某项，或声明「**以本机为准**」时，才移除对应仅文档项（「以本机为准」移除全部 kept_absent 类项），并报告 `removed`。
4. **两边都有的 `repos[]`（按 path）**：`branch` / `purpose` ← 本机盘点；`remotes` 按名并集——先保留文档中已有 remote 的相对顺序，再追加仅本机有的 remote（仅本机新仓则保留本机 `git remote` 顺序）。同名 remote **URL 不同**时：暂留**文档 URL**，报告 `remote_conflict`（含 path、name、doc_url、local_url），待用户确认后再改写。
5. **两边都有的 `symlinks[]`（按 path）**：规范化后 `target` **相同** → 用本机 `target` / `outside_ancestor`；**不同** → 暂留文档值，报告 `symlink_conflict`，待用户确认。
6. **损坏 / 版本不符停止写回**：若 README 已存在，但机器块无法解析或 `version` ≠ `1`，**禁止覆盖写回**，保留原文件，并向用户报告解析错误。

## 人读部分（短模板）

机器块之后（或之前均可，但机器块须可被注释定位）包含：

1. 标题：`# 工作区 Git 仓库来源`
2. 盘点日期（与 `inventoried_at` 一致）
3. **边界说明**：根据是否有祖先、独立仓数量、软连接，用几句自动生成
4. **目录结构**：仅仓库边界相关的 `text` 树
5. **独立仓库与远程**：Markdown 表，列：`目录 | 用途 | 分支 | 远程名 | 远程地址`（全部远程；同行目录可多行）
6. 若有祖先：**祖先仓库（勿混用）** 短表 + 勿混用提醒；表中路径须相对工作区根，**禁止绝对路径**
7. 若有软连接：逐条说明相对 target；`outside_ancestor: true` 时标注「非祖仓、拉取不创建、需人工确保」；拉取 skill **不创建**软连接；路径**禁止绝对路径**
8. 若某仓同时有 Gitee `origin` 与名为 `github` 的 GitHub 远程，且属本工作区约定的镜像仓（如 `fan-skills`）：写 **推送与镜像约定** 短节（见下）
9. **维护约定**（固定条文，见下）

### 推送与镜像约定（条件写入）

当 `repos[]` 中存在同时具备 Gitee `origin` 与 `github`（GitHub）远程的仓时，人读部分增加一节，至少写明：

- 日常推送只走 Gitee `origin`。
- 对该仓 **无需也不要对 `github` push**；Gitee 已配置自动同步到 GitHub。
- `github` 远程仅用于对照 / `fetch`。

### 维护约定固定条文

- 新增、移除或迁移独立仓库，以及增删远程时，重新运行文档生成 skill 覆盖本 README。
- **保留闸门**：仅文档有、本机无的仓/软连接默认保留并报告 `kept_absent`；不得无确认缩小清单。
- **删除闸门**：仅当用户点名删除或声明「以本机为准」时，才移除仅文档项并报告 `removed`。
- 独立子仓的 Git 操作使用 `git -C <dir> ...`，勿误用到祖先工作区。
- 日常推送默认走各仓 `origin`；其它远程用于上游对照/fetch，除非用户明确要求否则不对其 push。
- 若已写入「推送与镜像约定」：维护约定中可再点一句「Gitee → GitHub 自动同步，勿对 `github` push」。
- `.git-origin/` 可由祖先仓跟踪；独立子仓目录应由工作区根 `.gitignore` 忽略（本契约不强制改 ignore；用户明确要求时再改）。
- 不记录 commit hash，以免过期。
- 路径一律相对工作区根；**禁止绝对路径**。

## 拉取语义（供 pull skill）

前提：机器块 `version` 为 `1`。默认处理**全部** `repos[]`；用户点名时仅处理**精确匹配**子集（`repos[].path` 全等，或 `repos[].purpose` 全等）；无精确匹配的点名项列入报告且**不得猜测**扩大范围；未点名条目记入 `not_in_scope`（本机缺失也不 clone）。汇报区分 `selected` 与 `not_in_scope`。

对每个纳入范围的 `repos[]` 条目：

| 本地状态 | 行为 |
| --- | --- |
| 目录不存在 | `git clone`：远程优先名 `origin`，否则取 `remotes` **第一个**；clone 到 `path`。然后对其余 remote：`remote add` + `fetch` |
| 目录存在且为 Git 仓 | 对每个 remote：名不存在则 `remote add` 再 `fetch`；名存在且 URL 与文档一致则 `fetch`；名存在但 URL 不一致则**停止**，请用户确认 |
| 软连接 `symlinks[]` | **不创建**、不修改；汇报列出需人工确保的项；`outside_ancestor: true` 须明确标为非祖仓、勿盲建 |
| 依赖嵌套 `.git` | 文档中不应出现；忽略 |

只 `fetch`，不 `merge` / `rebase` / `pull`，不按 `branch` checkout。
