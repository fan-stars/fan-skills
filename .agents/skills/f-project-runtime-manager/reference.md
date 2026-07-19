# Project Runtime Manager — Reference

Agent 在生成脚本前按本节做探测与契约对齐。下列伪代码是**决策启发式**，不是可复制硬编码模板。

## 1. 后端探测

### 1.1 构建系统

```text
IF exists pom.xml → Maven
ELSE IF exists build.gradle OR build.gradle.kts → Gradle
ELSE → 非 Java 后端（跳过或标为未知）
```

### 1.2 Spring Boot 与可执行模块

Maven：

- 读根/子模块 `pom.xml`：`packaging`、`spring-boot-maven-plugin`、`modules`。
- 可执行候选：含 Boot 插件的模块，或含 `*Application.java` 且带 `@SpringBootApplication` 的模块。
- 多模块启动编译：`mvn -pl <module> -am package -DskipTests`（或项目已有等价命令，优先复用 README/AGENTS 中的命令）。
- 运行方式优先顺序（按探测选一）：
  1. `java -jar <module>/target/<finalName>.jar`（finalName 来自 pom）
  2. `mvn -pl <module> -am spring-boot:run`（开发态）

Gradle：

- 读 `settings.gradle*` 的 `include`，找 `org.springframework.boot` 插件模块。
- 编译：`./gradlew :<module>:bootJar` 或 `build`。
- 运行：`java -jar` 产物或 `./gradlew :<module>:bootRun`。

### 1.3 配置外置（只读推断）

只读 `application*.yaml|yml`、`bootstrap*`、文档中的约定，**复制需要的键到** `scripts/config/`：

| 机制 | 启动参数 / 环境变量示例 |
|------|-------------------------|
| Spring Boot 2.4+ | `--spring.config.additional-location=file:scripts/config/backend-local.yaml` |
| 覆盖 location | `SPRING_CONFIG_LOCATION=classpath:/,file:scripts/config/backend-local.yaml` |
| 单键覆盖 | `SPRING_DATASOURCE_PASSWORD=...`（写入 `backend.env` 再 `set -a; source`） |

禁止改仓库内 `src/main/resources` 配置。

### 1.4 端口与健康检查

- 从外置或只读配置取 `server.port`；未知则 status 只报 PID。
- 可选：`curl -sf "http://127.0.0.1:${PORT}/actuator/health"`（存在 actuator 时）。

## 2. 前端探测

### 2.1 包管理器

```text
pnpm-lock.yaml → pnpm
yarn.lock → yarn
package-lock.json → npm
ELSE packageManager 字段 → 按其值
ELSE 默认 npm（并在注释中标明置信度低）
```

### 2.2 框架与脚本

- `dependencies`/`devDependencies` 中 `vue`：解析 major → Vue2 / Vue3。
- 存在 `vite` 或 `vite.config.*` → Vite。
- 存在 `nuxt` 或 `nuxt.config.*` → Nuxt。
- 读 `package.json` `scripts`：优先 `dev`，其次 `serve`；构建用 `build`。
- Monorepo（pnpm-workspace / turbo / nx / lerna）：定位可 `dev` 的 app 包（如 `apps/*`），记录**在包根还是仓库根**执行命令。

### 2.3 配置外置

- 将需要覆盖的 `VITE_*` / `NUXT_*` 写入 `scripts/config/frontend.env`。
- 启动：`set -a; source scripts/config/frontend.env; set +a` 后执行包管理器脚本。
- 不修改 `.env`、`.env.local`、`package.json`、Vite/Nuxt 配置文件。

### 2.4 端口

只读 `vite.config.*` 的 `server.port`、`.env*` 中的 `PORT`/`VITE_PORT`，写入 status 与日志说明。

## 3. 进程与 PID 契约

### 3.1 路径约定

```text
RUN_DIR=$PROJECT_ROOT/scripts/run
LOG_DIR=$PROJECT_ROOT/scripts/logs
PID_FILE=$RUN_DIR/<app_id>.pid
LOG_FILE=$LOG_DIR/<app_id>.log
```

`app_id` 来自探测（如 `backend`、`frontend-web-antd`），小写、连字符。

### 3.2 优雅停止算法

```text
1. IF PID_FILE exists:
     pid=$(cat PID_FILE)
     IF process alive AND belongs_to_app(pid):
       kill -TERM pid
       wait up to N seconds (default 20–30)
       IF still alive: kill -KILL pid
     remove PID_FILE if process gone
2. ELSE precise match:
     find PIDs where:
       - cmdline matches expected pattern (jar name / main class / vite/node script), AND
       - cwd is under PROJECT_ROOT (via /proc/<pid>/cwd 或等价)
     IF exactly one match → 同上 TERM→KILL
     IF multiple → 拒绝自动杀，打印列表并退出非零
3. NEVER: killall, pkill, killall -9 java, pkill -f spring
```

`belongs_to_app`：核对 `/proc/<pid>/cmdline` 与启动时记录的模式；可选校验 cwd。

### 3.3 启动写 PID

- 后台启动（`nohup ... >> LOG_FILE 2>&1 &`），`echo $! > PID_FILE`。
- 短暂等待后 `kill -0 $(cat PID_FILE)`；失败则 `tail` 日志并退出非零。
- 打印：app_id、pid、log、config、推断端口。

## 4. common.sh 建议能力

生成 `scripts/lib/common.sh` 时包含可复用函数（名称可调整，语义保留）：

| 函数 | 职责 |
|------|------|
| `project_root` | 由脚本位置解析根目录 |
| `ensure_dirs` | 创建 run/logs/config |
| `load_env_file` | source 外置 env |
| `is_pid_running` | `kill -0` |
| `pid_belongs` | cmdline/cwd 校验 |
| `graceful_stop` | 第三节算法 |
| `require_cmd` | java/mvn/node/pnpm 等缺失时报错 |

## 5. 多应用命名

| 场景 | 命名 |
|------|------|
| 一后端一前端 | `backend-*.sh` / `frontend-*.sh` |
| 多后端 | `backend-<module>-*.sh` |
| 多前端 | `frontend-<app>-*.sh` 或统一 `frontend.sh <app> <action>` |
| 工作区多仓库 | 各仓库自有 `scripts/`；可选工作区 `scripts/workspace-*.sh` 调用子项目 |

## 6. 禁止清单（复查）

- [ ] 未修改任何已有配置 / package / pom / gradle / vite 文件
- [ ] 无 `killall` / `pkill`
- [ ] start 含编译步骤
- [ ] 仅相对路径 + 基于脚本位置的根解析
- [ ] 配置仅来自 `scripts/config/`
- [ ] PID 与日志落在 `scripts/run`、`scripts/logs`
