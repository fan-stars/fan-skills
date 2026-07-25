---
name: f-project-runtime-manager
description: >-
  Analyzes Java/Spring Boot and Vue/Vite project structures and generates
  portable start/stop/restart/status scripts under scripts/ with external
  configs in scripts/config/, without modifying existing project files.
  Use when the user asks to create project runtime scripts, start/stop
  managers, local launch scripts, backend/frontend process managers,
  project-runtime-manager, or unified project startup scripts.
---

# Project Runtime Manager

通过分析当前仓库结构，自动生成统一的项目启动管理脚本。**禁止使用固定模板或硬编码路径/命令**；一切启动命令、模块名、包管理器与配置加载方式均来自对当前项目的探测结果。

## 硬性约束

1. **先分析，后生成**：必须先完成结构探测与清单确认，再写脚本。
2. **禁止改动已有项目文件**：不得修改 `application*.yml|yaml`、`bootstrap*.yml|yaml`、`.env*`、`package.json`、`vite.config.*`、`nuxt.config.*`、`pom.xml`、`build.gradle*`、`settings.gradle*` 等。仅可在 `scripts/` 下新增文件。
3. **配置外置**：运行配置一律写入 `scripts/config/`，启动时通过 CLI 参数或环境变量加载。
4. **相对路径**：脚本内路径相对项目根目录解析，具备跨机器可移植性。
5. **安全停进程**：优先 PID 文件；其次精准匹配（命令行 + cwd/工作目录）；**禁止** `killall` / `pkill` / 模糊 `kill -9 $(pgrep ...)`。
6. **启动前必编译**：Java 走 Maven/Gradle；前端走检测到的 npm/pnpm/yarn（必要时先 install，再 build/dev 所需步骤）。

## 工作流程

复制并跟踪进度：

```text
Task Progress:
- [ ] 1. 确定管理根目录
- [ ] 2. 探测后端（Java）
- [ ] 3. 探测前端（Vue）
- [ ] 4. 输出探测清单给用户确认（多应用时）
- [ ] 5. 生成 scripts/ 骨架与 config
- [ ] 6. 生成 start/stop/restart/status（及可选 all）
- [ ] 7. 本地 dry-run / status 校验
- [ ] 8. 向用户汇总路径与用法
```

### Step 1：确定管理根目录

- 若工作区是「根目录 + 多个子仓库/子项目」，为每个含 `pom.xml` / `package.json` 的可运行根分别生成，或在工作区根生成可调用各子项目的聚合脚本（由探测结果决定，不强行套模板）。
- 单仓库：以该仓库根为 `PROJECT_ROOT`。

### Step 2：探测后端（Java）

按探测结果决策，详见 [reference.md](reference.md)。摘要：

| 信号 | 含义 |
|------|------|
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` + `settings.gradle*` | Gradle |
| `spring-boot-maven-plugin` / `spring-boot-gradle-plugin` / `@SpringBootApplication` | Spring Boot |
| 多模块：`modules` / `include` | 定位可执行模块（含 main 或 boot 插件） |
| 端口 / profile | 从现有配置**只读**推断，写入 `scripts/config/`，不改源文件 |

记录：构建工具、可执行模块、主类或最终 jar 路径模式、本地外置配置加载方式（如 `--spring.config.additional-location`）。

### Step 3：探测前端（Vue）

| 信号 | 含义 |
|------|------|
| `package.json` + `vue` 依赖 | Vue 项目 |
| `vue` major / `vite` / `nuxt` | Vue2/3、Vite、Nuxt |
| lockfile：`pnpm-lock.yaml` / `yarn.lock` / `package-lock.json` | 包管理器 |
| `scripts.dev` / `scripts.build` / monorepo `apps/*` | 启动与构建入口 |

记录：包管理器、dev/build 脚本名、应用工作目录（monorepo 子包）、端口（只读推断）。

### Step 4：确认清单（多项目时必做）

向用户简要列出将管理的应用，例如：

```text
Detected apps:
- backend: fan-server (Maven, Spring Boot, module fan-server)
- frontend: web-antd (pnpm, Vue3+Vite, app apps/web-antd)
```

用户可删减或改名；确认后再生成。

### Step 5–6：生成文件布局

仅新增（路径相对各 `PROJECT_ROOT`）：

```text
scripts/
├── lib/
│   ├── common.sh          # 路径、日志、PID、优雅停止
│   └── detect-or-env.sh   # 可选：读 scripts/config
├── config/
│   ├── backend.env        # 或 *.yaml，按项目需要
│   └── frontend.env
├── backend-start.sh
├── backend-stop.sh
├── backend-restart.sh
├── backend-status.sh
├── frontend-start.sh
├── frontend-stop.sh
├── frontend-restart.sh
├── frontend-status.sh
├── start-all.sh           # 多应用时可选
├── stop-all.sh
└── status-all.sh
```

多后端/多前端时用显式名称：`backend-<name>-start.sh` 或子目录 `scripts/<app>/`，由探测命名，勿写死 `fan-server`。

**生成规则（必须遵守）**：

1. 每个脚本 `set -euo pipefail`，开头解析 `SCRIPT_DIR` → `PROJECT_ROOT`。
2. `start`：`stop`（若在跑）→ 编译 → 启动 → 写 PID → 健康检查/短等 → 打印结果。
3. `stop`：读 PID 文件 → 校验进程确属本应用 → `SIGTERM` → 等待 → 必要时再 `SIGKILL`（仅该 PID）→ 清理 PID。
4. `restart`：`stop` + `start`。
5. `status`：PID 文件 + 进程存活 + 可选端口，输出人类可读状态。
6. 日志目录：`scripts/logs/`（gitignore 建议在生成说明中提示，**不要**擅自改已有 `.gitignore` 除非用户同意）。
7. PID：`scripts/run/<app>.pid`。
8. 配置：从 `scripts/config/` 加载；示例值可从现有配置**复制推导**到新文件，禁止覆盖原文件。

### Step 7：校验

- `bash -n` 语法检查。
- 执行对应 `*-status.sh`（应安全、无副作用）。
- 向用户报告生成路径与一条最短使用示例。

## 使用示例

### 示例 1：用户说「生成项目启动管理脚本」

1. 扫描工作区根与一级子目录。
2. 发现 Maven 多模块 Spring Boot + pnpm Vue3 Vite monorepo。
3. 确认应用清单后，在各自项目根（或工作区约定根）写入 `scripts/`。
4. 回复用法：

```bash
# 后端
./scripts/backend-start.sh
./scripts/backend-status.sh
./scripts/backend-stop.sh

# 前端
./scripts/frontend-start.sh
./scripts/frontend-restart.sh
```

### 示例 2：仅后端单体 Spring Boot

探测到单 `pom.xml` + `@SpringBootApplication` → 只生成 backend 四件套；config 使用：

```bash
java -jar target/app.jar \
  --spring.config.additional-location=file:scripts/config/backend-local.yaml
```

（具体 jar 名与 main 模块以探测为准。）

### 示例 3：多前端应用

探测到 `apps/web-antd`、`apps/web-ele` → 生成：

- `scripts/frontend-web-antd-start.sh` …
- `scripts/frontend-web-ele-start.sh` …
- 或 `scripts/frontend.sh <app> start|stop|restart|status`

## 最佳实践

- **探测优先于习惯**：仓库里已有外置配置约定（如 `scripts/config/backend-local.yaml`）时，复用路径与加载参数，不另造冲突约定。
- **编译范围最小化**：多模块只编译可运行模块及其依赖（如 `mvn -pl <module> -am`），避免全仓库无意义重编。
- **开发态 vs 产物态**：前端本地默认用探测到的 `dev` 脚本；若用户明确要求 preview/prod，再用 `build` + `preview`。
- **密钥不入库**：`scripts/config/*` 中的敏感示例用占位符；可生成 `scripts/config/*.example` 供复制。
- **幂等生成**：再次执行本 Skill 时先读已有 `scripts/`，增量更新，避免无提示覆盖用户已改脚本。
- **输出清晰**：启动结束打印 `app`、`pid`、`log`、`port`（若已知）、`config` 路径。

## 可扩展点

| 扩展 | 说明 |
|------|------|
| 更多运行时 | Node API、Go、Python（同目录约定：`scripts/<runtime>-*.sh` + `config/`） |
| 健康检查 | HTTP `/actuator/health`、前端根 URL、TCP 端口探测 |
| 环境切换 | `APP_ENV=dev|test` 映射到不同 `scripts/config/*.env` |
| 聚合入口 | 工作区级 `scripts/workspace-start.sh` 按序启停多仓库 |
| systemd/Docker | 由同一探测清单生成 unit 或 compose（仍禁止改项目原配置） |
| Windows | 可选生成 `.ps1`，语义对齐 shell 版 |

扩展时仍须：先分析、只写 `scripts/`、外置配置、安全停进程、启动前编译。

## 详细参考

- 探测启发式、进程匹配、脚本契约：[reference.md](reference.md)
- 端到端生成样例（示意，非固定模板）：[examples.md](examples.md)

## 完成时输出

向用户交付：

1. 探测到的应用清单（构建工具 / 入口 / 配置加载方式）
2. 新增文件列表（均在 `scripts/` 下）
3. 最短启动/停止/状态命令
4. 明确声明：未修改任何项目既有配置与源文件
