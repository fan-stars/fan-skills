# AGENTS-CN.md

> 本文件是 [`AGENTS.md`](AGENTS.md) 的中文对应版。若两者存在冲突，以 `AGENTS.md` 为准。

## 项目概览

`fan-skills` 是 Fan 项目的 **Skills 目录库**，其他仓库可按技术栈从分类目录中挑选并复制 skill。它**不是**应用项目：没有应用服务器、基于 `package.json` 的应用构建，也没有产品代码测试套件。

| 路径 | 作用 |
| --- | --- |
| `.agents/skills/` | **真相源**（通过 `skills-lock.json` 安装/更新） |
| `skills-lock.json` | 第三方 skill 的上游安装锁 |
| `skills-catalog.json` | 仅保存分类映射与链接（**不保存中文文案**） |
| `skills/` | **只读派生产物**，按分类复制，每次全量清空重建 |
| `.cursor/skills/sync-skills-catalog/` | 同步运维 skill（**不进入** catalog，也**不复制到** `skills/`） |
| `.cursor/skills/sync-skills-catalog/generated/skill-docs.json` | AI 生成的中文说明缓存，以内容哈希为键 |
| `spec/` | 本地 OpenSpec 记录，已通过 `/spec` **忽略提交** |

当前规模约为：`.agents/skills/` 下约 36 个 skill；`skills/` 中允许多分类副本，例如 `frontend-design` 同时位于 `web/react` 与 `web/design`。

## 硬性规则（不得违反）

1. **禁止手工编辑** `skills/` 下的任何内容，必须通过同步流程重新生成。
2. **禁止在** `skills-catalog.json` 中加入中文简介字段，如 `descriptionZh`、`detailsZh` 等。
3. **禁止将** `sync-skills-catalog` 加入 `skills-catalog.json` 或复制进 `skills/`。
4. catalog 中的 skill 集合**必须等于** `.agents/skills/` 下的目录名集合，同步脚本会校验。
5. Fan 自研 skill 使用 `f-` 前缀，必须归入 `fan` 分类，也可以同时保留技术分类。
6. 第一期**不提供 presets** 预设包。
7. 提交信息优先使用中文，遵循近期历史风格：祈使、简洁、侧重原因。

## 环境与命令

维护本目录库无需安装 Node 应用依赖，需要：

- `python3`：运行同步脚本
- 网络与 `npx`：从 GitHub / skills.sh 安装或更新 skill

```bash
# 可选：刷新锁定的第三方 skills
npx skills update -y

# 查看哪些 skills 需要 AI 生成中文说明
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status

# skill-docs.json 完整后，全量清空并重建 skills/
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render

# 校验 catalog、说明缓存与 README 的一致性
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

此克隆的默认远程通常为 Gitee 的 `origin1`，推送前使用 `git remote -v` 确认。

## 开发流程

### 新增第三方 skill

```bash
npx skills add <owner/repo>            # 或 owner/repo/skill-name
# 确认 skills-lock.json 已更新
# 在 skills-catalog.json 增加 categories[]、skillsShUrl、githubUrl（可为 null）
# 依次执行：status → 为 NEED_GENERATE 生成说明 → render → validate
```

若上游仓库**没有** `SKILL.md`（例如仅在 registry 发布的 skill），可从 skills.sh 内容手工创建 `.agents/skills/<name>/SKILL.md`，按实际情况将 `githubUrl` 设为 `null`，然后执行同步。

### 新增 Fan 自研 skill

1. 创建 `.agents/skills/f-<name>/`，其中包含 `SKILL.md`，可附带 references。
2. 在 `skills-catalog.json` 中配置：
   - `categories`：必须包含 `"fan"`，并按需增加技术分类（如 `java`、`workflow`）
   - `skillsShUrl`：`null`
   - `githubUrl`：`null`，README 将链接到本仓库 `.agents/skills/...`
3. 生成中文说明，然后执行 `render` 与 `validate`。

### 仅修改分类

修改 `skills-catalog.json` 中的 `categories` 列表后执行 `render`。只要源内容哈希未变，就无需重新生成 AI 说明。

### 同步与中文 README 流程（必须按顺序）

1. 执行 `sync.py status`，读取 `NEED_GENERATE`；结果也会写入 `generated/status.json`。
2. 对列表中的每个 skill，读取 `.agents/skills/<name>/SKILL.md`，必要时再读取 references。**禁止仅凭名称臆测能力**。
3. 按 [GENERATION_PROTOCOL.md](.cursor/skills/sync-skills-catalog/docs/GENERATION_PROTOCOL.md) 写入或更新 `.cursor/skills/sync-skills-catalog/generated/skill-docs.json`：
   - 字段：`summary`、`capabilities`、`scenarios`、`coverage`、`notes`、`contentHash`
   - `contentHash` 必须与 `status.json` 中的哈希一致
   - 质量要求：中文 CJK；`summary` 长度不少于 24 且不含 `|`；其他字段长度不少于 40
4. 执行 `sync.py render`，再执行 `sync.py validate`，预期输出 `VALIDATE_OK`。

运维 skill 入口：`.cursor/skills/sync-skills-catalog/SKILL.md`。

## 分类

分类定义在 `skills-catalog.json` 的 `categories`：

| Key | 含义 |
| --- | --- |
| `web/react` | React / Next / Ant Design |
| `web/vue` | Vue / Nuxt / Vben |
| `web/design` | 视觉设计与 UI 规范 |
| `java` | Spring Boot / Java 重构 |
| `spec` | OpenSpec / 规格说明 |
| `docs` | 办公文档（docx/pdf/pptx/xlsx） |
| `workflow` | 规划、质询、领域建模、find-skills |
| `mcp` | MCP Server 构建 |
| `testing` | Web / 浏览器自动化测试 |
| `fan` | Fan 自研、非公开开源项目的 skills |

一个 skill 可以声明**多个分类**，同步时会把完整 skill 目录复制到每个分类中。

## 将 skill 复制到其他项目

1. 浏览 `skills/<category>/README.md`，查看总览表和详细介绍。
2. 将所需 skill 文件夹复制到目标项目的 `.agents/skills/`。
3. 如果目标项目使用 `skills-lock.json`，按需补充 lock 条目。
4. 不要把 `skills/` 当作可编辑源；修改应在**本仓库** `.agents/skills/` 中进行，然后同步。

## 测试说明

本项目没有单元测试或端到端测试套件。对 Agent 而言，“测试”是：

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

同步后还应检查：

- 多分类 skill 出现在所有声明分类中，且内容完全一致。
- Fan skill 的 skills.sh 显示「暂无」，GitHub 显示「本仓库」链接。
- `.cursor/skills/sync-skills-catalog` 未出现在 `skills/` 下。
- 幂等性：源与说明未变时，第二次 `render` 不应产生有意义的差异。
- 内容变更：修改某个 skill 文件后，`status` 的 `NEED_GENERATE` 应只列出该 skill。

## 代码与内容风格

- Catalog JSON：仅保存稳定元数据（`categories`、`skillsShUrl`、`githubUrl`）；新增条目时保持 skill key 按字母排序。
- AI 说明：使用中文，遵循 GENERATION_PROTOCOL 的长度与 CJK 要求。
- 派生 README：由 `sync.py` 生成，禁止手工格式化。
- `.gitignore`：使用 `/spec`（仅仓库根目录）和 `.idea`；**禁止使用裸 `spec`**，否则会误忽略 `skills/spec/`。

## 构建与发布

本项目没有生产构建。“发布”流程为：

1. 同步，确保 `skills/` 与生成说明为最新状态。
2. 提交 catalog、`.agents/skills`、lock、同步工具与重新生成的 `skills/`。
3. 推送到已配置远程；若跟踪远程为 `origin1`，使用 `git push origin1 HEAD`。

禁止提交密钥。除非用户明确修改忽略策略，否则不得提交已忽略的 `spec/`。

## Pull Request 与提交规范

- 提交信息使用简洁中文，重点说明“为什么”，可参考 `git log`。
- catalog、skills 或说明有变化时，提交前必须执行 `sync.py validate`。
- 同步输出变化时，应同时提交源文件（`.agents/skills`、catalog、lock、`skill-docs.json`）与派生产物 `skills/**`。
- amend 或 force push 前必须询问；禁止修改 Git 配置。

## 调试与常见问题

- 有 skill 需要生成说明时，`status` 返回码为 **2**，这是预期行为，不是脚本崩溃。
- 任一 skill 缺少有效 AI 说明时，`render` 会直接失败，不会静默回退为 skill 名称。
- 一次向 `npx skills add` 传入多个包时，可能只安装第一个；应逐个安装。
- 部分 skills.sh 条目在 GitHub 仓库中没有 `SKILL.md`；可手工安装/创建，并在 catalog 中设 `githubUrl: null`。
- 工具型 skills（`agent-browser`、`next-browser`、`extract-design-system`）在消费项目实际使用时还需要额外 CLI / 浏览器依赖；本仓库只保存 skill 文本。
- `spec/` 下的本地 OpenSpec 仅供维护者规划，不属于对外发布的分类目录。

## 补充说明

- 面向人的概览见 [README.md](README.md)，其内容可能略有滞后；Agent 应优先以本文件、`AGENTS.md` 与 `skills/README.md` 为准。
- 重新生成中文说明时，应优先复用 `skill-docs.json` 中 `contentHash` 未变化的条目，避免无意义差异。
