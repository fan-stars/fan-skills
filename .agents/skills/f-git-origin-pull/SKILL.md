---
name: f-git-origin-pull
description: >-
  按 .git-origin/README.md 中 YAML 机器块拉取独立 Git 仓：缺则 clone，有则补 remote 并 fetch；
  不 merge/rebase/pull、不 checkout、不创建软连接。用于按远程文档拉项目、恢复工作区子仓。
---

# f-git-origin-pull

按文档机器块恢复/更新独立 Git 工作树。解析规则与字段见同伴契约：

[f-git-origin-doc/reference.md](../f-git-origin-doc/reference.md)

## 何时使用

- 用户要求按 `.git-origin` / 远程文档拉取、克隆、同步子仓远程
- 在新机器上按已有文档恢复工作区仓

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
- [ ] 逐个处理 repos[]
- [ ] 跳过 symlinks[]（仅汇报）
- [ ] 汇报成功 / 跳过 / 待确认项
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

### 2. 处理每个 repo

`dir = <工作区根>/<repos[].path>`。

#### 2.1 目录不存在

1. 选 clone URL：`remotes` 中 `name == origin` 的 url；若无 `origin`，用 **列表第一个** remote 的 url  
2. `git clone <url> <dir>`  
3. 对尚未存在的其余 remote：`git -C <dir> remote add <name> <url>` 然后 `git -C <dir> fetch <name>`  
4. 若 clone 所用 remote 名不是文档中的名（极少见），按文档把远程名调整到一致（`remote rename` / `add`），保证文档中每个 name 都存在且 URL 一致后再 fetch

#### 2.2 目录存在

1. 确认 `<dir>` 是 Git 工作树；否则停止该条目并报告  
2. 对文档中每个 remote：
   - 本地无该名：`git remote add <name> <url>` → `git fetch <name>`
   - 本地有该名且 URL 相同（比较 fetch URL）：`git fetch <name>`
   - 本地有该名但 URL 不同：**停止**，输出文档 URL vs 本地 URL，等待用户确认（确认改 URL 后再 `set-url` + `fetch`；确认保留本地则跳过该 remote）

### 3. 软连接

对 `symlinks[]`：不创建、不删除、不改 target；在汇报中列出「需人工确保」。

### 4. 汇报

按仓列出：cloned / fetched remotes / skipped / awaiting-confirmation。勿声称已合并或已切换分支。
