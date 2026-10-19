---
name: f-site-rewrite-init
description: >-
  Portable site-rewrite initializer: ships scaffold/ inside the skill, copies it
  to repo-root site-rewrite/ on init, then fills legacy/reference/rewrite URLs,
  dataApis, secrets refs, source trees, framework/UI library. Use when starting
  a frontend rewrite, "重构初始化", "f-site-rewrite-init", or before
  f-site-rewrite-implement. Install with f-site-rewrite-implement for full flow.
---

# f-site-rewrite-init

为「对照旧站 / 参考站 → 用新框架 + UI 库重写」在**当前项目根**建立工作区 `site-rewrite/`。

本 skill 为自研工作流（`f-` 前缀），**可单独拷贝到其他仓库**使用：骨架目录在 skill 内 [`scaffold/`](scaffold/)，**初始化时再复制到项目根**，不必预先存在 `site-rewrite/`。

未完成 init **不得**进入 `f-site-rewrite-implement`（请与本 skill 成对安装）。

**配置与文档必须通用**：不得写入某一客户站、品牌或域名作为硬编码默认值。

## When to use

- 用户说：重构初始化、site-rewrite init、`f-site-rewrite-init`、开始重写某站
- 项目根尚无 `site-rewrite/refactor.config.yaml`

## 移植安装

将下列目录拷到目标仓库的 skills 路径即可（本仓为 `.agents/skills/`）：

```
f-site-rewrite-init/          # 本目录（含 scaffold/）
f-site-rewrite-implement/     # 成对安装
```

无需附带任何业务仓库的 `site-rewrite/`；首次 init 会生成。

## Hard rules

1. **先复制骨架，再填配置**：`scaffold/` → 项目根 `site-rewrite/`（见第 1 步）。  
2. **交互收集**：缺字段就问；路径是否存在可自行核对，决策交给用户。  
3. **密钥**：只写入 gitignore 的 secrets；配置里仅路径引用。  
4. **多参考站 / 多数据接口**：数组配置。  
5. **完成后**：提示调用 `f-site-rewrite-implement`（未要求跳步则不得跳过）。

## Workflow

```
Init Progress:
- [ ] 1. 将 skill 内 scaffold/ 复制到项目根 site-rewrite/
- [ ] 2. 收集站点 / 数据接口 / 源码 / 示例 / 技术栈
- [ ] 3. 收集鉴权 → secrets.local.env
- [ ] 4. 填写 refactor.config.yaml（保留中文注释）
- [ ] 5. 确认 indexes/、data-apis/ 等骨架文件齐全
- [ ] 6. 确认 site-rewrite/.gitignore 含 secrets
- [ ] 7. 向用户确认配置摘要（密钥打码）
```

### 1. 落点：从 skill 复制骨架

**真相源**：本 skill 目录下的 [`scaffold/`](scaffold/)（随 skill 分发）。

**目标**：当前工作区 / 仓库根目录的 `site-rewrite/`。

执行（Agent 必须实际跑命令，勿只口述）：

```bash
# <SKILL_DIR> = 本 SKILL.md 所在目录（含 scaffold/）
# <REPO_ROOT> = 用户指定的项目根（默认当前工作区根）

SKILL_DIR="…/f-site-rewrite-init"
REPO_ROOT="…"

if [ ! -d "$SKILL_DIR/scaffold" ]; then
  echo "missing scaffold/; skill install incomplete" >&2
  exit 1
fi

if [ ! -d "$REPO_ROOT/site-rewrite" ]; then
  cp -a "$SKILL_DIR/scaffold" "$REPO_ROOT/site-rewrite"
else
  # 已存在：只补缺失文件，禁止覆盖 secrets.local.env 与用户已填配置（除非用户明确要求重置）
  # 可用: cp -an "$SKILL_DIR/scaffold/." "$REPO_ROOT/site-rewrite/"
  echo "site-rewrite/ already exists — merge missing files only; do not clobber secrets"
fi

# 若尚无本地密钥文件，从 example 复制空壳（仍 gitignore）
if [ ! -f "$REPO_ROOT/site-rewrite/secrets.local.env" ] \
   && [ -f "$REPO_ROOT/site-rewrite/secrets.local.env.example" ]; then
  cp "$REPO_ROOT/site-rewrite/secrets.local.env.example" \
     "$REPO_ROOT/site-rewrite/secrets.local.env"
fi
```

复制后的树：

```
site-rewrite/                    ← 项目根（运行时工作区）
  README.md
  .gitignore
  refactor.config.yaml
  secrets.local.env.example
  indexes/ …
  data-apis/ …
  observations/ matches/ playbooks/
```

skill 内仍保留 `scaffold/` 作为模板，**不要**在业务提交里删掉 skill 的 scaffold。

### 2. 必填字段

| 字段 | 说明 |
| --- | --- |
| `projectId` | 短 id（用户给定） |
| `legacySite` | 要重构的网站（访客前台） |
| `referenceSites[]` | 参考站，可多个 |
| `rewriteSite` | 重构后本站（可多环境） |
| `dataApis[]` | **数据接口**（源平台取数 API） |
| `sourceTrees[]` | 旧站源码目录（只读） |
| `exampleProjects[]` | 新栈示例 / 模板 |
| `target.framework` / `uiLibrary` / `appRoot` | 目标技术栈 |
| `auth` | secrets 引用；可无需登录 |
| `skills.uiLibrary` | UI 库 skill 名 |

可选：`quality.matchThreshold`（默认 **0.95**）、`commitLanguage: zh`、`skills.proposal`。

### 3. 鉴权

写入 `site-rewrite/secrets.local.env`（可用 [secrets.example.env](secrets.example.env) 对照）：

```bash
LEGACY_USER=
LEGACY_PASSWORD=
LEGACY_COOKIE=
# DATA_API_<ID>_X_API_TOKEN=
```

### 4. 填写配置

1. 以 [config.template.yaml](config.template.yaml) 与已复制的 `site-rewrite/refactor.config.yaml` 为准填写。  
2. **保留中文注释**。  
3. 勿把密钥写进 yaml。

### 5. 确认输出

```
骨架来源: <SKILL_DIR>/scaffold/
工作区: <REPO_ROOT>/site-rewrite/refactor.config.yaml
下一步: 使用 f-site-rewrite-implement（勿跳步）
```

## Do not

- 不要在 init 写业务 UI 或 OpenSpec 提案  
- 不要把真实站点名/域名写进 skill / scaffold 默认值  
- 不要假设框架或 UI 库  
- 不要在「已存在 site-rewrite」时静默覆盖 `secrets.local.env`  

## Additional resources

- [scaffold/](scaffold/) — 复制到项目根的完整骨架  
- [config.template.yaml](config.template.yaml)  
- [secrets.example.env](secrets.example.env)  
- [indexes.md](indexes.md)  
- [data-api-record-template.md](data-api-record-template.md)  
- [PACKAGING.md](PACKAGING.md) — 如何打包给其他项目
