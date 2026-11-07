# Project Runtime Manager — Examples

下面用虚构名字展示两种 Java 布局。目录名、应用名、端口、jar 路径不可照抄。换一个仓库必须重新探测，再按探测到的布局选择命令。

## A. 单模块 Java

候选根 `ledger` 自身含有 `pom.xml` 和 `spring-boot-maven-plugin`。`application.yaml` 的 `spring.application.name` 是 `ledger`，`server.port` 是 8080。`finalName` 来自该 pom。脚本基名是 `ledger`，工作目录就是 `ledger`。

```bash
./scripts/runtime/macos/ledger-start.sh
./scripts/runtime/macos/ledger-start.sh jar
```

`ledger-start.sh` 不带参数时，在 `ledger` 执行：

```bash
mvn spring-boot:run
```

`ledger-start.sh jar` 在 `ledger` 执行 `mvn package -DskipTests`，再运行 `java -jar target/ledger.jar`。这里的 jar 文件名来自探测到的 `finalName`，不来自子目录。

Gradle 单模块对应 `./gradlew bootRun` 与 `./gradlew bootJar`。

## B. 多模块 Java

只有可执行单元的构建文件在候选根的子目录中时，才使用这一组命令。在 reactor 根执行：

```bash
mvn -pl <module> -am -DskipTests install
mvn -pl <module> org.springframework.boot:spring-boot-maven-plugin:<version>:run
mvn -pl <module> -am package -DskipTests
java -jar <module>/target/<finalName>.jar
```

第二行不要加 `-am`。`<version>` 来自该模块 pom 里插件版本解析后的值。

Gradle 对应 `./gradlew :<module>:bootRun` 与 `./gradlew :<module>:bootJar`。

脚本基名仍是该单元的 `spring.application.name`，不是父目录名加子目录名。`<module>` 是探测到的相对模块路径。不要把某一套父子目录写进技能或别的项目。

## C. Node

`order-web` 是虚构的 pnpm 仓库。根 `scripts.dev` 是 `pnpm -F @example/shop-console run dev`，所以 Node 主入口是 `shop-console`，命令在 `order-web` 根执行。`shop-mobile` 在 `apps/` 下，根 `dev` 没有引用，只写进探测说明，不生成脚本。

```bash
./scripts/runtime/macos/shop-console-start.sh
```

`node_modules` 缺失时先 `pnpm install`，然后执行上面的 dev 命令。向它传入 `jar` 会以退出码 2 结束。

## D. 同时存在两类主入口

在 macOS 上默认只写 `scripts/runtime/macos/`。单模块 Java 与 Node 都存在时，再生成 `start-all.sh`、`stop-all.sh` 和 `status-all.sh`。`start-all.sh` 先启动 Java，再启动 Node。

```text
os: macos
apps:
- ledger: Maven, Spring Boot, single-module, mode default run, jar target/ledger.jar, server.port 8080
- shop-console: pnpm, Vue, script dev, package @example/shop-console
not generated:
- shop-mobile

用法：
  ./scripts/runtime/macos/ledger-start.sh
  ./scripts/runtime/macos/ledger-start.sh jar
  ./scripts/runtime/macos/shop-console-start.sh

未修改项目既有配置与源文件。示例名字是虚构的。
```

用户明确要求 Linux 脚本时，只生成 `scripts/runtime/linux/`。Windows 则是 `scripts/runtime/windows/` 下的同名 `.ps1`，参数位置与 bash 相同。不要因为当前机器是 macOS 就额外写出另外两套。Linux 进程库见 F，原样复制 `templates/linux/common.sh`。Windows 进程库见 H，原样复制 `templates/windows/common.ps1`。不要把 macOS 的 `common.sh` 复制到 linux 或 windows。

## E. macOS 拼装

进程库使用技能里的 `templates/macos/common.sh`，原样复制为 `scripts/runtime/macos/lib/common.sh`。不要改写。虚构的单模块身份写成 `lib/app-ledger.sh`：

```bash
APP_NAME="ledger"
APP_KIND="java"
APP_PORT_DEFAULT="8080"
APP_PORT_VAR="SERVER_PORT"
REACTOR_REL="ledger"
UNIT_REL="ledger"
MAIN_CLASS="com.example.ledger.LedgerApplication"
FINAL_NAME="ledger"
JAR_REL="ledger/target/ledger.jar"
JAVA_REQUIRED=""
JAVA_PREPARE_ARGV=()
JAVA_RUN_ARGV=(mvn spring-boot:run)
JAVA_PACKAGE_ARGV=(mvn package -DskipTests)
```

`MAIN_CLASS` 用全限定名。多模块时 `JAVA_PREPARE_ARGV` 是带 `-am` 的 `install`，`JAVA_RUN_ARGV` 是不带 `-am` 的 `spring-boot-maven-plugin:<version>:run`。

虚构的 Node 身份使用同一套入口，标记不要写成包管理器包装进程。Vite 的 `APP_CMD_MARKER` 是 `vite/bin/vite`：

```bash
APP_NAME="shop-console"
APP_KIND="node"
APP_PORT_DEFAULT="5173"
APP_PORT_VAR="VITE_PORT"
APP_CMD_MARKER="vite/bin/vite"
WORK_REL="order-web"
PACKAGE_REL="order-web/apps/shop-console"
NODE_PM="pnpm"
NODE_ARGV=(pnpm -F @example/shop-console run dev)
```

`ledger-start.sh` 只做这几步：

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
. "$SCRIPT_DIR/lib/common.sh"
. "$SCRIPT_DIR/lib/app-ledger.sh"
runtime_start "$@"
```

`stop`、`restart`、`status` 把最后一行换成 `runtime_stop`、`runtime_restart "$@"` 或 `runtime_status "$@"`。这些目录名和命令都不可照抄，必须换成本次探测结果。

## F. Linux 拼装

进程库使用技能里的 `templates/linux/common.sh`，原样复制为 `scripts/runtime/linux/lib/common.sh`。不要改写，也不要改成某一份项目脚本。不要把 `templates/macos/common.sh` 复制过来。

ledger 与 shop-console 的字段和上面的 macOS 示例相同，只是目录换成 `scripts/runtime/linux/`。

```bash
./scripts/runtime/linux/ledger-start.sh
./scripts/runtime/linux/ledger-status.sh
./scripts/runtime/linux/shop-console-start.sh
```

`ledger-status.sh` 最后一行是 `runtime_status "$@"`。这些名字是虚构的，必须换成本次探测结果。

## G. 示例环境变量

`config/ledger.env.example` 只含收集到的占位符和固定键。口令值是 `change-me`，其他键为空。注释里的缺省是虚构的。

```bash
PORT_WAIT_SECONDS=
# 配置缺省 5432
LEDGER_DB_PORT=
# 配置有缺省，不写入缺省口令
LEDGER_DB_PASSWORD=change-me
# 模块要求 JDK 17
JAVA_HOME=
```

`JAVA_HOME` 只在 `JAVA_REQUIRED` 非空时出现。`SERVER_PORT` 不写入赋值。这些名字必须换成本次探测结果。加载时跳过空值和 `change-me`。

## H. Windows 拼装

进程库使用技能里的 `templates/windows/common.ps1`，原样复制为 `scripts/runtime/windows/lib/common.ps1`。不要改写，也不要改成某一份项目脚本。不要把 bash 的 `common.sh` 翻译进 windows。

Windows 解析命令时优先 `.exe`，其次 `.cmd`、`.bat`。只有 `.ps1` 时用 `powershell.exe -File`。失败时退出文本是「命令失败」，日志按 UTF-8 读取，错误输出按 UTF-8 书写。Java 启动要带上 `sun.stdout.encoding=UTF-8` 和 `stdout.encoding=UTF-8`，`System.out` 才不会按代码页 936 写入日志。

入口脚本是同名 `.ps1`，参数位置与 bash 相同。ledger 与 shop-console 的字段和 E 相同。语法停在 Windows PowerShell 5.1。

```powershell
powershell -NoProfile -File .\scripts\runtime\windows\ledger-start.ps1
powershell -NoProfile -File .\scripts\runtime\windows\ledger-start.ps1 jar
powershell -NoProfile -File .\scripts\runtime\windows\ledger-status.ps1
powershell -NoProfile -File .\scripts\runtime\windows\shop-console-start.ps1
```

`ledger-start.ps1`：

```powershell
$ErrorActionPreference = 'Stop'
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORKSPACE_ROOT = (Resolve-Path (Join-Path $SCRIPT_DIR '..\..\..')).Path
. (Join-Path $SCRIPT_DIR 'lib\common.ps1')
. (Join-Path $SCRIPT_DIR 'lib\app-ledger.ps1')
runtime_start @args
```

`stop`、`restart`、`status` 把最后一行换成 `runtime_stop`、`runtime_restart @args` 或 `runtime_status`。`lib/app-ledger.ps1` 使用与 E 相同的虚构字段，数组写成 `@('mvn', 'spring-boot:run')`。`MAIN_CLASS` 仍是 `com.example.ledger.LedgerApplication`。`lib/app-shop-console.ps1` 的 `APP_CMD_MARKER` 仍是 `vite/bin/vite`。这些名字是虚构的，必须换成本次探测结果。

`start-all.ps1` 先调用 ledger，再调用 shop-console。`stop-all.ps1` 与 `status-all.ps1` 同样在每次调用后检查退出码。非法参数的用法提示写当前入口名，例如 `ledger-start.ps1`，不要写成 `start-all.ps1`。

```powershell
$ErrorActionPreference = 'Stop'
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

& (Join-Path $SCRIPT_DIR 'ledger-start.ps1') @args
if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $SCRIPT_DIR 'shop-console-start.ps1')
if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```
