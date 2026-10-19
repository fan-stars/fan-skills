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
  path: "<绝对路径或空字符串>"
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
    target: "/absolute/or/relative/target"
```
<!-- git-origin-manifest:end -->
```

### 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `version` | 是 | 固定 `1` |
| `inventoried_at` | 是 | 盘点日 `YYYY-MM-DD` |
| `workspace` | 是 | 工作区根目录名 |
| `ancestor.path` | 是 | 向上解析到的 Git 根；无则 `""` |
| `ancestor.has_gitlink` | 是 | 祖先索引是否含本工作区 gitlink（`160000`） |
| `repos[].path` | 是 | 相对工作区根，POSIX，无尾斜杠 |
| `repos[].purpose` | 是 | 短用途；可用目录名，勿编造长业务文案 |
| `repos[].branch` | 是 | 盘点时当前分支名；**拉取时不 checkout** |
| `repos[].remotes` | 是 | **全部**远程；至少 1 项；顺序保留 `git remote` 顺序 |
| `repos[].remotes[].name` | 是 | 远程名 |
| `repos[].remotes[].url` | 是 | fetch URL（与 push 不同时仍记 fetch） |
| `symlinks` | 是 | 无则 `[]` |
| `symlinks[].path` | 是 | 相对工作区根 |
| `symlinks[].target` | 是 | `readlink` 结果 |

### 不写入 `repos` 的路径

依赖安装树内嵌套 `.git`（如 `vendor/`、`node_modules/` 下）**排除**，不写机器块、不当独立仓。

`reference/` 等容器本身不是 Git 时：不写特殊容器章节；其下独立 Git 目录照常进 `repos`。

## 人读部分（短模板）

机器块之后（或之前均可，但机器块须可被注释定位）包含：

1. 标题：`# 工作区 Git 仓库来源`
2. 盘点日期（与 `inventoried_at` 一致）
3. **边界说明**：根据是否有祖先、独立仓数量、软连接，用几句自动生成
4. **目录结构**：仅仓库边界相关的 `text` 树
5. **独立仓库与远程**：Markdown 表，列：`目录 | 用途 | 分支 | 远程名 | 远程地址`（全部远程；同行目录可多行）
6. 若有祖先：**祖先仓库（勿混用）** 短表 + 勿混用提醒
7. 若有软连接：逐条说明「绝对/相对软连接；拉取 skill 不创建」
8. 若某仓同时有 Gitee `origin` 与名为 `github` 的 GitHub 远程，且属本工作区约定的镜像仓（如 `fan-skills`）：写 **推送与镜像约定** 短节（见下）
9. **维护约定**（固定条文，见下）

### 推送与镜像约定（条件写入）

当 `repos[]` 中存在同时具备 Gitee `origin` 与 `github`（GitHub）远程的仓时，人读部分增加一节，至少写明：

- 日常推送只走 Gitee `origin`。
- 对该仓 **无需也不要对 `github` push**；Gitee 已配置自动同步到 GitHub。
- `github` 远程仅用于对照 / `fetch`。

### 维护约定固定条文

- 新增、移除或迁移独立仓库，以及增删远程时，重新运行文档生成 skill 覆盖本 README。
- 独立子仓的 Git 操作使用 `git -C <dir> ...`，勿误用到祖先工作区。
- 日常推送默认走各仓 `origin`；其它远程用于上游对照/fetch，除非用户明确要求否则不对其 push。
- 若已写入「推送与镜像约定」：维护约定中可再点一句「Gitee → GitHub 自动同步，勿对 `github` push」。
- `.git-origin/` 可由祖先仓跟踪；独立子仓目录应由工作区根 `.gitignore` 忽略（本契约不强制改 ignore；用户明确要求时再改）。
- 不记录 commit hash，以免过期。

## 拉取语义（供 pull skill）

对每个 `repos[]` 条目：

| 本地状态 | 行为 |
| --- | --- |
| 目录不存在 | `git clone`：远程优先名 `origin`，否则取 `remotes` **第一个**；clone 到 `path`。然后对其余 remote：`remote add` + `fetch` |
| 目录存在且为 Git 仓 | 对每个 remote：名不存在则 `remote add` 再 `fetch`；名存在且 URL 与文档一致则 `fetch`；名存在但 URL 不一致则**停止**，请用户确认 |
| 软连接 `symlinks[]` | **不创建**、不修改 |
| 依赖嵌套 `.git` | 文档中不应出现；忽略 |

只 `fetch`，不 `merge` / `rebase` / `pull`，不按 `branch` checkout。
