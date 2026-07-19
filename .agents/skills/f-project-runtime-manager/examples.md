# Project Runtime Manager — Examples

以下为**示意**：真实脚本中的模块名、包管理器、jar 名、端口必须来自探测，不可原样照抄。

## A. Maven 多模块 + Spring Boot（示意）

**探测结果（示例）：**

- 根：`pom.xml`，模块 `app-server`
- 主类：`com.example.AppApplication`
- 外置配置：`--spring.config.additional-location=file:scripts/config/backend-local.yaml`

**生成后用法：**

```bash
./scripts/backend-start.sh
./scripts/backend-status.sh
./scripts/backend-restart.sh
./scripts/backend-stop.sh
```

**start 流程（逻辑，非模板）：**

1. `source scripts/lib/common.sh`
2. `graceful_stop backend`
3. `mvn -pl app-server -am package -DskipTests`
4. `nohup java -jar app-server/target/app-server.jar --spring.config.additional-location=file:scripts/config/backend-local.yaml >> scripts/logs/backend.log 2>&1 &`
5. 写 `scripts/run/backend.pid`，校验存活并打印结果

## B. pnpm + Vue3 + Vite monorepo（示意）

**探测结果（示例）：**

- `pnpm-lock.yaml`，workspace 含 `apps/web-antd`
- `package.json` scripts：`dev:antd` → 在仓库根执行
- 端口：5666（只读自 Vite 配置）

**生成：**

- `scripts/config/frontend.env`（如 `VITE_GLOB_API_URL=...` 占位）
- `scripts/frontend-start.sh`：stop → `pnpm install`（若需要）→ `pnpm dev:antd` 后台 → PID

```bash
./scripts/frontend-start.sh
./scripts/frontend-status.sh
```

## C. 工作区双仓库（示意）

```text
workspace/
├── backend-repo/scripts/...
└── frontend-repo/scripts/...
```

可选在 `workspace/scripts/start-all.sh` 中依次调用：

```bash
"$ROOT/backend-repo/scripts/backend-start.sh"
"$ROOT/frontend-repo/scripts/frontend-start.sh"
```

仍分别为各仓库生成完整四件套，聚合脚本只做编排。

## D. 向用户交付的回复格式

```text
探测：
- backend: <module> (Maven / Spring Boot)
- frontend: <app> (pnpm / Vue3 / Vite)

新增（均在 scripts/ 下）：
- lib/common.sh
- config/backend-local.yaml.example
- config/frontend.env.example
- backend-{start,stop,restart,status}.sh
- frontend-{start,stop,restart,status}.sh

用法：
  ./scripts/backend-start.sh
  ./scripts/frontend-start.sh

未修改项目既有配置与源文件。
```
