---
name: f-git-origin-doc
description: >-
  Use when generating or updating .git-origin/README.md, inventorying
  independent Git repos or symlinks in a workspace, or refreshing
  cross-machine repo-origin docs. Do not use for git clone/fetch of those repos
  (use f-git-origin-pull).
---

# f-git-origin-doc

读旧机器块 → 与本机盘点合并 → 覆盖写回工作区 `.git-origin/README.md`。格式、字段与合并语义以 [reference.md](reference.md) 为契约权威；本文件是触发与流程清单，不得替代契约全文。

## 何时使用

- 用户要求生成/更新 `.git-origin/README.md`、仓库来源盘点、跨机器刷新 origin 文档
- 独立子仓或软连接变更后需刷新文档（默认合并保留，非整表按本机重写）

## 不要做

- 无删除指令时**不得**因本机缺失删除 `repos` / `symlinks`（默认保留并报告 `kept_absent`）
- **不得**写入本机绝对路径（`ancestor.path`、`symlinks[].target`、人读部分均须相对工作区根）
- 默认**不要**修改根 `.gitignore`（仅当用户明确要求时再改）
- 不要把依赖树内嵌套 `.git`（`vendor/`、`node_modules/` 等）写入 `repos`
- 不要记录 commit hash
- 不要提交 git，除非用户明确要求
- **不得**以全局技能拷贝为编辑真相源（权威在内容库 `fan-skills/.agents/skills/`；用 sync 同步到 Cursor/agents 等全局技能根，禁止手改全局拷贝）
- 契约细节以 [reference.md](reference.md) 为准；禁止只读 description / 本清单就动手写回

## 反模式

| 借口 | 现实 |
| --- | --- |
| 本机没有就是该删 | 跨机器清单；默认保留并报告 `kept_absent` |
| 整表重写更干净 | 禁止无确认缩小清单；须读旧→合并→写回 |
| 绝对路径更准确 | 跨机器失效；必须相对化到工作区根 |
| description 已说明流程 | 必须读全文与 [reference.md](reference.md) |

## 流程

```text
- [ ] 确定工作区根
- [ ] 若存在 README：提取机器块；无法解析或 version≠1 则停止写回
- [ ] 盘点本机独立仓与软连接（路径相对化）
- [ ] 解析祖先为相对工作区根路径
- [ ] 与旧机器块合并（保留 kept_absent；remotes 并集；冲突上报）
- [ ] 仅当用户明确删除或「以本机为准」时缩小清单
- [ ] 覆盖写入 README（禁绝对路径）
- [ ] 向用户报告 added / kept_absent / conflicts / removed / normalized_paths
```

### 1. 确定工作区根与读旧

默认当前 Cursor 工作区根；用户指定则用之。

若 `.git-origin/README.md` 已存在：

1. 提取 `<!-- git-origin-manifest:start -->` … `end` 内 YAML
2. 若无法解析或 `version` ≠ `1`：**禁止覆盖写回**，保留原文件，向用户报告解析错误后停止
3. 解析成功则保留旧 `repos` / `symlinks` / `remotes` 供后续合并

### 2. 盘点独立 Git 目录

在工作区根下查找 `.git`（文件或目录）。

**排除**路径中含以下段的命中（依赖嵌套）：

- `vendor`
- `node_modules`
- `.pnpm`
- `bower_components`

每个命中目录视为独立仓（不是 submodule 假定；若祖先索引对该路径为 `160000` 仍照常记入文档并在边界说明中写明）。

对每个仓收集（路径一律相对工作区根，POSIX，无尾斜杠）：

- `path`：相对工作区根
- `branch`：`git -C <dir> branch --show-current`（空则 `HEAD` 短哈希或 `DETACHED`）
- `remotes`：`git -C <dir> remote -v` 的 **全部** fetch URL，保留 remote 顺序
- `purpose`：短字符串（目录名或仓名即可）

### 3. 软连接

工作区根下（建议 `find` maxdepth 合理或递归但跳过已排除依赖段）收集符号链接：

- `path`：相对工作区根
- `target`：由 `readlink` 结果**换算为相对工作区根**的 POSIX 路径；**禁止**写入绝对路径
- `outside_ancestor`：规范化 target 落在祖先根之外（无祖先则落在工作区根之外）时为 `true`；否则 `false`
- 写入 `symlinks`；人读部分各写一小段「拉取不创建」；`outside_ancestor: true` 时标注「非祖仓、拉取不创建、需人工确保」

### 4. 祖先

```bash
git rev-parse --show-toplevel
```

若成功：将返回的绝对路径**换算为相对工作区根**后写入 `ancestor.path`（如 `..`）；**禁止**写入绝对路径。检查祖先是否对本工作区（或子路径）存在 mode `160000` gitlink → `has_gitlink`。  
失败：`path: ""`，`has_gitlink: false`。

### 5. 与旧机器块合并

按 [reference.md](reference.md)「更新语义」：

1. **读旧 → 合并 → 写回**：禁止仅按本机盘点整表覆盖导致丢条目
2. **kept_absent**：旧机器块有、本机不存在的 `repos[]` / `symlinks[]` 默认保留，报告 `kept_absent`（软连接可用 `kept_absent_symlink`）
3. **删除闸门**：仅当用户**点名删除**某项，或声明「**以本机为准**」时，才移除对应仅文档项（「以本机为准」移除全部 kept_absent 类项），并报告 `removed`。无此类指令时**不得**缩小清单
4. **两边都有的仓**：`branch` / `purpose` ← 本机；`remotes` 按名并集（先文档顺序，再追加仅本机有的）；同名 URL 不同则暂留文档 URL，报告 `remote_conflict`（path、name、doc_url、local_url）
5. **两边都有的软连接**：规范化 target 相同 → 用本机 `target` / `outside_ancestor`；不同 → 暂留文档值，报告 `symlink_conflict`
6. 本机新增仓/软连接记入 `added`；相对化过程中改写过的路径记入 `normalized_paths`

### 6. 覆盖写入 README

1. 确保 `.git-origin/` 存在
2. **整文件覆盖** `.git-origin/README.md`（内容为合并后的完整文档，非「仅本机盘点」）
3. 必须含契约规定的 `<!-- git-origin-manifest:start -->` … `end` YAML 块
4. 人读部分用契约短模板；有祖先则加「勿混用」节；有软连接则逐条说明
5. 若某仓同时有 Gitee `origin` 与 `github` 远程：按 reference 写入「推送与镜像约定」（Gitee 自动同步 GitHub，勿 push `github`）
6. `reference/` 容器本身不写专项大章；其下独立仓已在 `repos` 即可
7. 机器块与人读部分均**禁止绝对路径**

### 7. 汇报

向用户报告：

- `added` / `kept_absent`（或 `kept_absent_symlink`）/ `conflicts`（含 `remote_conflict` / `symlink_conflict`）/ `removed` / `normalized_paths`
- 写入的仓数、远程数、软连接数、文件路径
- 提醒 pull 使用 `f-git-origin-pull`

## 用户明确要求改 ignore 时

仅在用户明确说要忽略文件/同步 `.gitignore` 时：把各 `repos[].path` 以 `/<path>/` 形式写入工作区根 `.gitignore`（保留已有非仓条目），并忽略 `.idea/`、`.vscode/`、`.DS_Store` 等常见本地文件；**不要**忽略 `.cursor/` 或 `.git-origin/`。
