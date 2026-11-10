# f-skills sync 共享契约

`f-skills-audit` / `f-skills-sync-out` / `f-skills-promote` / `f-skills-apply` 共同遵守本文。进 git 的配置与 journal **禁止**机器绝对路径。

## 逻辑 target

| 逻辑名 | 默认路径模板 | 可写 | audit |
| --- | --- | --- | --- |
| `agents` | `~/.agents/skills` | 是 | 是 |
| `cursor` | `~/.cursor/skills` | 是 | 是 |
| `codex` | `~/.codex/skills` | 是 | 是 |
| `cursor-store` | `cursor-store://detect`（运行时探测） | 否（第一期） | 可探测则只读 |

永不作为可写 target：`~/.cursor/skills-cursor`、工具目录下 `.system`。

路径只允许：`~/...`、`$HOME/...`、相对库根、`cursor-store://...` 逻辑值。禁止写入机器相关绝对路径（Unix 家目录根路径、root 盘绝对路径、Windows 盘符路径）到 `skills-sync.yaml` 或 journal。

## 职责表

| 意图 | 使用 |
| --- | --- |
| 只对比、不写盘 | `f-skills-audit` |
| 库 → 全局 | `f-skills-sync-out` |
| 已知单 skill 从逻辑 target 回写库 | `f-skills-promote` |
| 批量扫描多根入库 | `f-skills-library-ingest` |
| 按 journal 跨机对齐全局 | `f-skills-apply`（只回放 `sync-out`） |

## 传输与覆盖

- 默认 **copy**。symlink 仅同机显式 opt-in；**跨机 apply 一律 copy**。
- 目标已存在：contentHash 相同 → 跳过；不同 → 报告分歧并确认后再覆盖（可用 CLI `--yes`）。

## contentHash

算法与仓内 `.cursor/skills/sync-skills-catalog/scripts/sync.py` 的 `content_hash` 对齐：

- 相对 skill 根路径排序后拼接文件字节做 sha256
- 忽略目录：`__pycache__`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`、`.venv`
- 忽略文件：`.DS_Store`；后缀 `.pyc` / `.pyo`

实现：`scripts/sync_lib.py` → `content_hash`。

## exclude

`skills-sync.yaml` 的 `exclude.names` 与内置系统名录合并。至少排除 `sync-skills-catalog` 及 Cursor/Codex 产品同步类 skill 名（见 `DEFAULT_SYSTEM_EXCLUDE`）。

## profile

`include.names` ∪（`include.categories` 在 `skills-catalog.json` 中命中的 skill）∩ 真相源目录存在 − exclude。

`default` profile **必须**包含：`f-skills-audit`、`f-skills-sync-out`、`f-skills-promote`、`f-skills-apply`。

## Journal（A1）

- 相对库根目录：`skills-sync-journal/`（由 `skills-sync.yaml` → `journal.path` 指定）
- `promote` 成功后必须再写一条 `action: sync-out`（伴生）
- `apply` **只**回放 `sync-out`；裸 `promote` 不写全局
- 字段只用逻辑 target 名与 `library_rel`；本机已应用记在 `$HOME/.config/fan-skills/applied.json`

## Bootstrap（B1）

新机器：clone 本库后，将上述四个 skill 目录拷到本机 `~/.cursor/skills`（及需要的 `agents`/`codex`），或在已有入口时执行：

```bash
python3 .agents/skills/f-skills-audit/scripts/cli.py sync-out --library . --profile default --yes
```

之后可用 `apply` 回放 journal。
