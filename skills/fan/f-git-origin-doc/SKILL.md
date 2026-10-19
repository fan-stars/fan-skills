---
name: f-git-origin-doc
description: >-
  盘点工作区内独立 Git 仓与软连接，覆盖生成 .git-origin/README.md（含 YAML 机器块与人读短文）。
  用于生成/更新远程来源文档、git-origin、工作区仓库边界盘点；不默认修改 .gitignore。
---

# f-git-origin-doc

覆盖生成工作区 `.git-origin/README.md`。格式与字段以 [reference.md](reference.md) 为准。

## 何时使用

- 用户要求生成/更新远程文档、`.git-origin`、仓库来源盘点
- 独立子仓或远程变更后需刷新文档

## 不要做

- 默认**不要**修改根 `.gitignore`（仅当用户明确要求时再改）
- 不要把依赖树内嵌套 `.git`（`vendor/`、`node_modules/` 等）写入 `repos`
- 不要记录 commit hash
- 不要提交 git，除非用户明确要求

## 流程

```text
- [ ] 确定工作区根（默认当前 Cursor 工作区根；用户指定则用之）
- [ ] 盘点独立 Git 目录与软连接
- [ ] 解析祖先 Git 与 gitlink
- [ ] 覆盖写入 .git-origin/README.md
- [ ] 向用户汇报结果摘要
```

### 1. 盘点独立 Git 目录

在工作区根下查找 `.git`（文件或目录）。

**排除**路径中含以下段的命中（依赖嵌套）：

- `vendor`
- `node_modules`
- `.pnpm`
- `bower_components`

每个命中目录视为独立仓（不是 submodule 假定；若祖先索引对该路径为 `160000` 仍照常记入文档并在边界说明中写明）。

对每个仓收集：

- `path`：相对工作区根
- `branch`：`git -C <dir> branch --show-current`（空则 `HEAD` 短哈希或 `DETACHED`）
- `remotes`：`git -C <dir> remote -v` 的 **全部** fetch URL，保留 remote 顺序
- `purpose`：短字符串（目录名或仓名即可）

### 2. 软连接

工作区根下（建议 `find` maxdepth 合理或递归但跳过已排除依赖段）收集符号链接：

- `path`、`target`（`readlink`）
- 写入 `symlinks`；人读部分各写一小段「拉取不创建」

### 3. 祖先

```bash
git rev-parse --show-toplevel
```

若成功：写入 `ancestor.path`；检查祖先是否对本工作区（或子路径）存在 mode `160000` gitlink → `has_gitlink`。  
失败：`path: ""`，`has_gitlink: false`。

### 4. 覆盖写入 README

1. 确保 `.git-origin/` 存在
2. **整文件覆盖** `.git-origin/README.md`
3. 必须含契约规定的 `<!-- git-origin-manifest:start -->` … `end` YAML 块
4. 人读部分用契约短模板；有祖先则加「勿混用」节；有软连接则逐条说明
5. `reference/` 容器本身不写专项大章；其下独立仓已在 `repos` 即可

### 5. 汇报

列出写入的仓数、远程数、软连接数、文件路径；提醒 pull 使用 `f-git-origin-pull`。

## 用户明确要求改 ignore 时

仅在用户明确说要忽略文件/同步 `.gitignore` 时：把各 `repos[].path` 以 `/<path>/` 形式写入工作区根 `.gitignore`（保留已有非仓条目），并忽略 `.idea/`、`.vscode/`、`.DS_Store` 等常见本地文件；**不要**忽略 `.cursor/` 或 `.git-origin/`。
