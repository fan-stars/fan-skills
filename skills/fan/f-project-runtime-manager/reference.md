# Project Runtime Manager — Reference

生成脚本前按本节决策。伪代码和函数体是契约，里面的模块名、包名、端口必须换成本次探测结果。

## 1. 候选根与构建工具

```text
候选 = 工作区根（若直接含构建文件） + 直接子目录（直接含构建文件）
跳过目录名：.tmp generated worktrees .worktree node_modules dist target
有 pom.xml → Maven
没有 pom.xml 且有 build.gradle 或 build.gradle.kts → Gradle
```

不进入子目录再找第二个项目根。直接子目录若出现在父构建文件的 Maven `<modules>` 或 Gradle `include` 中，它属于父候选根，不是独立候选根。

## 2. Java 主入口与基名

可执行模块满足任一条件：

- `pom.xml` 含 `spring-boot-maven-plugin`
- Gradle 插件 `org.springframework.boot`
- 源码含 `@SpringBootApplication`

恰好一个构建单元才生成。零个跳过 Java。多于一个时打印路径并退出本次生成。

布局只在候选根上判断。构建文件就在候选根的，是单模块，命令在候选根执行。构建文件在该候选根的子目录里的，是多模块，命令仍在候选根执行。父 POM 只表示坐标继承、候选根自身又能启动时，仍按单模块处理。列在父模块清单里的子目录不是单模块候选根。

基名顺序：`src/main/resources/application.yaml`、`application.yml`、`application.properties` 的 `spring.application.name`，然后 `artifactId`，然后模块目录名。基础文件已有名字时忽略 `application-<profile>.*` 里的同名键。忽略 compose 与命令行覆盖。

基名折成小写，连续的非 `[a-z0-9]` 收成一个连字符，去掉首尾连字符。

## 3. Node 主入口与基名

读候选根的根级 `package.json`。优先 `scripts.dev`，没有则 `scripts.start`。用下面这些形式从脚本文本取出唯一包名或目录：

- `pnpm -F <name>`
- `pnpm --filter <name>`
- `turbo run <script> --filter <name>`
- `turbo run <script> --filter=<name>`
- `npm run <script> --workspace <name>`
- `yarn workspace <name>`
- `cd <dir>` 之后的包管理器命令

`dev:extra`、`build`、`preview` 不增加应用。根脚本不存在，且多个子包有 `dev` 时，打印这些子包并退出本次生成。只有一个这样的子包时采用它。

包管理器：`pnpm-lock.yaml` → pnpm；`yarn.lock` → yarn；`package-lock.json` → npm；否则 `packageManager` 字段；否则 npm，并在探测说明里标明置信度低。

工作目录：根脚本通过 filter 或 workspace 调用时，在候选根执行。脚本本身位于包目录时，在该包目录执行。

基名取包 `name` 的 scope 之后一段。`@example/shop-console` 变为 `shop-console`。没有 `name` 时用文件夹名。折规则与 Java 相同。基名相撞时把父目录名加在后面，例如两个 `shop` 分别变成 `shop-apps` 与 `shop-packages`。

运行时标签只看依赖名：`react`、`next`、`vue`、`nuxt`、`@angular/core`、`svelte`、`astro`、`express`、`fastify`、`koa`、`@nestjs/core`。都没有时写 Node。标签不改变命令。

## 4. 命令

默认模式名是 `run`。

单模块在候选根执行：

| 模式 | Maven | Gradle |
| --- | --- | --- |
| `run` | `mvn spring-boot:run` | `./gradlew bootRun` |
| `jar` | `mvn package -DskipTests`，再 `java -jar target/<finalName>.jar` | `./gradlew bootJar`，再 `java -jar` 到 bootJar 产物 |

多模块在 reactor 根执行，且只在可执行单元是子目录时使用：

| 模式 | Maven | Gradle |
| --- | --- | --- |
| `run` | 先 `mvn -pl <module> -am -DskipTests install`，再 `mvn -pl <module> org.springframework.boot:spring-boot-maven-plugin:<version>:run` | `./gradlew :<gradlePath>:bootRun` |
| `jar` | `mvn -pl <module> -am package -DskipTests`，再 `java -jar <module>/target/<finalName>.jar` | `./gradlew :<gradlePath>:bootJar`，再 `java -jar` 到该子项目的 bootJar 产物 |

`<module>` 是 Maven `-pl` 使用的相对路径。`<gradlePath>` 把同一相对路径中的 `/` 换成 `:`，例如 `a/b` 写成 `:a:b:bootRun`。

多模块的 `run` 不要把 `spring-boot` 短前缀和 `-am` 写在同一条 `mvn` 里。聚合 POM 上常常没有这个插件前缀。完整插件目标如果和 `-am` 写在一起，`run` 会在父 POM 上执行并因没有主类失败。`install` 负责把 reactor 依赖装进本地仓库；随后的 `run` 只选择可执行模块，并且不加 `-am`。

`<version>` 读可执行模块 pom 里该插件的 `<version>`。值是 `${spring.boot.version}` 这类属性时，用该模块实际继承到的属性值替换。不要把属性名原样写进命令。

`<finalName>` 读可执行单元的构建文件。Maven 常见写法是 `<finalName>${project.artifactId}</finalName>`，这时用该模块的 `artifactId` 替换。单模块的 jar 在候选根 `target/<finalName>.jar`。多模块的 jar 在 `<module>/target/<finalName>.jar`。读不到时停止生成并说明缺哪一个字段，不要猜文件名，也不要把字面量 `${...}` 传给 `java -jar`。

`run` 的参数从 `config/<app>.env` 以环境变量传入。只有项目原来就使用 `--spring.config.additional-location` 时，才把同等参数指到 `scripts/runtime/<os>/config/` 下的同名文件。

Node：`node_modules` 不存在时，在工作目录执行一次该包管理器的 install，然后执行探测到的 `dev` 或 `start`。不执行 `build`。

入口脚本的第一个参数：

| 参数 | 行为 |
| --- | --- |
| 省略或 `run` | Java 走 `run`；Node 走 `dev` 或 `start` |
| `jar` | 仅 Java。Node 打印用法并以退出码 2 结束 |
| 其它 | 打印用法并以退出码 2 结束 |

`<app>-restart` 不带参数时读取 `run/<app>.mode`；文件不存在则用 `run`。`<app>-restart jar` 与 `<app>-restart run` 强制该模式。`stop` 与 `status` 不读取模式参数。

## 5. 目录

`macos/` 与 `linux/`：

```text
scripts/runtime/<os>/
├── lib/common.sh
├── config/<app>.env.example
├── config/<app>.env
├── run/
├── logs/
├── <app>-start.sh
├── <app>-stop.sh
├── <app>-restart.sh
├── <app>-status.sh
├── start-all.sh
├── stop-all.sh
└── status-all.sh
```

两个主入口都存在时才生成三个 `*-all` 脚本。`start-all` 先调用每个 Java 入口的 start，再调用每个 Node 入口的 start。前一个非零则停止后续调用。

`windows/` 把 `.sh` 换成 `.ps1`，公共库是 `lib/common.ps1`。参数位置与 bash 相同。三个汇总脚本仍按 bash 的顺序调用入口，但每次 `&` 之后要看 `$LASTEXITCODE`。子脚本正常结束时这个值可能仍是空，空不是失败；非 0 就 `exit` 这个码。`$ErrorActionPreference = 'Stop'` 接不住子脚本里的 `exit`。

example 从可执行模块 `src/main/resources` 的基础配置收集占位符。基础文件是实际存在的 `application.yaml`、`application.yml` 或 `application.properties`。再读 `spring.profiles.active` 的第一个字面 profile，文件名为同目录的 `application-<profile>`，扩展名与基础文件相同。先去掉注释和引号；逗号分隔或列表只取第一个。该值本身是 `${...}` 时，只读基础文件，并在探测说明里写明 profile 没有解析。不读其他 profile 文件，不读 `target/classes`。profile 文件应当存在却缺失时，停止生成并说明缺哪一个。

不读注释。只收集 `${NAME}` 和 `${NAME:缺省}`，且 `NAME` 匹配 `[A-Z][A-Z0-9_]*`。同名只写一次。基础文件和 profile 都有缺省时，注释用 profile 的缺省。

名字含 `PASSWORD`、`SECRET`、`TOKEN`、`ACCESS_KEY`、`PRIVATE_KEY` 或 `_KEY` 的，值写 `change-me`。注释只说明配置里有缺省，不抄缺省口令。其余键值留空，注释写配置缺省。

example 始终包含空的 `PORT_WAIT_SECONDS=`。`JAVA_REQUIRED` 非空时另写空的 `JAVA_HOME=`，注释只写要求的主版本。不导出 `SERVER_PORT`。脚本加载 env 时跳过空值和 `change-me`，避免覆盖项目自带配置。真实 env 不存在时复制 example，已存在则不覆盖。

端口只读：Java 读生效配置里的 `server.port`；Vite 读 `server.port`；Next 读脚本中的 `-p` 或 `PORT`。status 在读到端口时打印它。

工作区根 `.gitignore` 追加：

```gitignore
scripts/runtime/*/config/*.env
!scripts/runtime/*/config/*.env.example
scripts/runtime/*/run/
scripts/runtime/*/logs/
```

某行已经存在则不要重复追加。

## 6. 进程文件

`macos` 的进程控制以 [templates/macos/common.sh](templates/macos/common.sh) 为准，生成时原样复制为 `scripts/runtime/macos/lib/common.sh`。`linux` 的进程控制以 [templates/linux/common.sh](templates/linux/common.sh) 为准，生成时原样复制为 `scripts/runtime/linux/lib/common.sh`。`windows` 的进程控制以 [templates/windows/common.ps1](templates/windows/common.ps1) 为准，生成时原样复制为 `scripts/runtime/windows/lib/common.ps1`。不要改写这三份进程库，也不要跨系统复制。6.2 与 6.3 是 bash 进程库的行为；平台差别在 6.5、6.6 与 6.7。

| 文件 | 内容 |
| --- | --- |
| `run/<app>.pid` | 应用进程 PID |
| `run/<app>.launcher.pid` | 仅 `run` 模式的 Maven 或 Gradle PID |
| `run/<app>.mode` | `run` 或 `jar` |
| `logs/<app>.log` | 标准输出与标准错误 |

`jar` 模式不写 launcher 文件。

### 6.1 bash 入口如何定位工作区

`lib/common.sh` 放在 `scripts/runtime/<os>/lib/common.sh`。入口脚本这样解析：

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=/dev/null
. "$SCRIPT_DIR/lib/common.sh"
```

`common.sh` 若自行解析，向上四级：

```bash
workspace_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "$here/../../../.." && pwd)
}
```

生成时把探测到的相对路径写进入口脚本，例如单模块 `APP_DIR="$WORKSPACE_ROOT/ledger"`。`ledger` 只是虚构示例，必须换成探测到的目录名。多模块另外记录 reactor 根和 `<module>` 相对路径，不把这两段拼成固定的父子目录名。

### 6.2 run 模式记录 fork 出的 JVM

长时间进程放进新会话再后台运行，输出追加到 `logs/<app>.log`。macOS 没有 `setsid` 命令时，用 Python `os.setsid()` 后 `exec`。只做 `nohup` 不够，启动脚本所在的进程组结束时会把服务一起收掉。把新会话的 PID 写入 `run/<app>.launcher.pid`。然后最多 60 秒，每秒只在该启动器的子孙进程里寻找恰好一个 Java 进程。排除启动器自身。该进程还要同时满足：

- 工作目录在可执行单元目录之下
- 命令行包含应用主类名

找到这一个时，把它的 PID 写入 `run/<app>.pid`，并把 `run` 写入 `run/<app>.mode`。超时，或匹配数不是 1：只对本次 launcher PID 发送 `kill -TERM`，等待 25 秒后仍在则只对它 `kill -KILL`。然后打印日志末尾并退出非零。不要碰其它 Java 进程。

macOS 读工作目录用 `lsof -a -p <pid> -d cwd`，读命令行用 `ps -p <pid> -ww -o command=`。不要省略 `-ww`，长 classpath 会被截断，主类名会落在被截掉的部分。Linux 读 `/proc/<pid>/cwd` 与 `/proc/<pid>/cmdline`。生成 linux 脚本时不要重写这段读取，原样复制 `templates/linux/common.sh`。

`jar` 模式同样放进新会话再后台运行 `java -jar`。命令行通常没有主类名，用 jar 路径识别：包含 `<module>/target/<finalName>.jar` 或 `target/<finalName>.jar`。工作目录是启动它的目录，多模块即 reactor 根，单模块即候选根。只把该 PID 写入 `run/<app>.pid`，模式文件写 `jar`。

Node 的应用进程是 dev server 本身，不是包管理器包装进程。Vite 要求命令行包含 `vite/bin/vite`，且工作目录在该包目录。`pnpm vite` 这类包装进程只算启动器。

### 6.3 停止

1. 读取 `run/<app>.pid`。
2. 进程仍在，且命令行与工作目录都属于该应用时，`kill -TERM`。
3. 等待 25 秒。
4. 仍在时只对这个 PID `kill -KILL`。
5. `run` 模式对仍属于本次启动的 `run/<app>.launcher.pid` 重复 2–4。
6. 进程结束后删除对应 PID 文件。

没有 PID 文件，或文件里的进程已经不在时，只用命令行加工作目录寻找。恰好一个才按上面的顺序停止。零个则说明已经停止。多于一个则打印列表并以非零退出。禁止 `killall`、`pkill`、`taskkill /IM java`。

停掉 Node 应用进程后，沿父进程向上。父进程的命令行属于这次的包管理器，且工作目录是候选根或该包目录时，用同样的 TERM、等待、KILL 停掉它。遇到 PID 1，或父进程不属于该应用，就停止上溯。不要停 IDE 或其他无关父进程。

`start` 发现应用 PID 仍属于本应用时，先完成停止，再按本次参数启动。只有确认本 PID 正在监听时，才打印应用名、模式、pid、日志路径、配置路径和端口。

### 6.4 Windows

进程库是 `templates/windows/common.ps1`，原样复制为 `scripts/runtime/windows/lib/common.ps1`。入口脚本是同名 `.ps1`，参数位置与 bash 相同。行为见 6.7。不要把 6.4 再写成另一份进程库。

### 6.5 macOS 模板

只用于 `scripts/runtime/macos/`。进程库是技能里的 `templates/macos/common.sh`，原样复制为 `lib/common.sh`。身份放在生成的 `lib/app-<app>.sh`。不要把项目名写进模板。

`lib/app-<app>.sh` 提供命令数组，例如 `JAVA_PREPARE_ARGV`、`JAVA_RUN_ARGV`、`JAVA_PACKAGE_ARGV` 或 `NODE_ARGV`。模板用 execvpe 执行这个数组。不要用 bash -c，不要用 nohup。没有 python3 且没有 setsid 时，启动失败并说明原因。

启动成功分三段：

1. 先停本应用里命令行和工作目录都核对得上的进程。端口上若还有其他 PID 在监听，列出这些 PID 并失败，不要杀掉它们。
2. 最多 60 秒，在启动器子孙里找到恰好一个应用进程。Java `run` 要有全限定主类名，且工作目录在可执行单元目录下。`jar` 用 `target/<finalName>.jar` 识别，工作目录是 reactor 根或该单元目录。Node 用 `APP_CMD_MARKER`；Vite 填 `vite/bin/vite`。超时或不是恰好一个时，只终止本次启动器。
3. 探测到端口时，从找到应用进程之后再等。默认最多 180 秒。`PORT_WAIT_SECONDS` 为空或 `change-me` 时用 180，不含前导零的正整数才覆盖。60 秒寻找应用进程的那段不改。四条结果：

   - 本 PID 已在该端口的监听者里：成功。`runtime_start` 这时才调用 `print_running`。
   - 进程在监听前退出：删除刚写的 PID、launcher、mode 文件，非零退出。
   - 等到上限，本进程还在，端口仍没人听：非零退出。保留 PID、launcher 和 mode，不杀进程，不调用 `print_running`。
   - 端口上出现别的 PID：立刻非零退出。保留自己的 PID、launcher 和 mode，不杀对方。本 PID 也在监听者里时算成功。

   没有探测到端口则跳过等待，启动成功，不调用 `print_running`。`print_running` 仍供 `runtime_status` 使用。

发现候选进程时用 `pgrep -f` 读取完整参数，再用 `ps -p <pid> -ww -o command=` 复核。跳过 `pgrep` 自己。停完再扫一次，仍有匹配进程就列出 PID 并失败。

Java 的 JAVA_REQUIRED 来自构建文件里的 java.version 或 release，没有则留空。已设置的 JAVA_HOME 满足该主版本就用它，不用更高版本替换。不满足时再用 `/usr/libexec/java_home`，然后才查找常见安装位置。找不到就失败，并提示写到 `config/<app>.env`。

example 按第 5 节收集。加载时跳过空值和 `change-me`。

### 6.6 Linux 模板

只用于 `scripts/runtime/linux/`。进程库是技能里的 `templates/linux/common.sh`，原样复制为 `lib/common.sh`。不要改写，也不要把 `templates/macos/common.sh` 复制过来。身份仍放在生成的 `lib/app-<app>.sh`。不要把项目名写进模板。

行为与 6.5 相同。bash 3.2：不用关联数组，不用 `${var,,}`，不依赖 `mapfile`。同一条 `local` 里不要引用刚声明的变量。用 execvpe 执行命令数组。不要用 bash -c，不要用 nohup。没有 python3 且没有 setsid 时，启动失败并说明原因。

启动分三段：先停命令行和工作目录都核对得上的本应用进程；端口上还有其他 PID 就列出并失败，不杀它们；60 秒内在启动器子孙里找到恰好一个应用进程；探测到端口后的等待与 6.5 第 3 段相同。没有探测到端口则跳过等待。Java `run` 要有全限定主类名，且工作目录在可执行单元目录下。`jar` 用 `target/<finalName>.jar` 识别，工作目录是 reactor 根或该单元目录。Node 用 `APP_CMD_MARKER`；Vite 填 `vite/bin/vite`。停完再扫一次，仍有匹配进程就列出 PID 并失败。父进程只沿本次的 pnpm、npm 或 yarn 上溯，遇到 PID 1 或不属于该应用就停止。已设置且主版本符合的 `JAVA_HOME` 直接使用，不用更高版本替换。找不到要求的 JDK 就失败。

和 macOS 的差别只有读取进程和查找 JDK。工作目录读 `/proc/<pid>/cwd`，命令行读 `/proc/<pid>/cmdline`。不要依赖 lsof，也不要调用 `/usr/libexec/java_home`。监听 PID 用 `ss -ltnp` 按本地端口读取。`ss` 没有给出 PID 时，再用 `/proc/net/tcp` 与 `/proc/net/tcp6` 确认端口是否已在监听；确认被占用但读不到 PID 就失败，不要去杀进程。候选进程可以用 `pgrep -f`，但必须再用 `/proc` 里的完整命令行复核，并跳过 pgrep 自己。JDK 只查已设置的 `JAVA_HOME`、当前 `java`，以及 `/usr/lib/jvm` 这类系统约定位置。不要写死家目录或某一台机器上的安装路径。

### 6.7 Windows 模板

只用于 `scripts/runtime/windows/`。进程库是技能里的 `templates/windows/common.ps1`，原样复制为 `lib/common.ps1`。不要改写，也不要把 bash 进程库翻译进 windows。身份放在生成的 `lib/app-<app>.ps1`。不要把项目名写进模板。

入口脚本是同名 `.ps1`。参数位置与 bash 相同：省略或 `run`、`jar` 仍是第一个参数。入口向上三级得到工作区根，点源 `lib/common.ps1` 和 `lib/app-<app>.ps1`，再调用 `runtime_start`、`runtime_stop`、`runtime_restart` 或 `runtime_status`。`usage_and_exit` 使用当前入口脚本的文件名。从调用栈由近到远找，跳过 `common.ps1`，不要取最外层的汇总脚本。

语法停在 Windows PowerShell 5.1。不要使用 PowerShell 7 才有的 `&&`、三元运算符和空值合并运算符。

行为与 6.5 相同。命令参数数组直接交给进程。解析命令时优先 `.exe`，然后 `.cmd`、`.bat`。无扩展名的同名文件不要拿来启动。只有 `.ps1` 垫片时，用 `powershell.exe -File` 执行它，后面仍是原来的参数。不要在模板里写 `cmd /c`。不要用 `taskkill /IM java`，也不要按进程名模糊停止。

同步命令若启动失败或退出码不是 0，把旁路输出并入 `logs/<app>.log`，删掉旁路文件，再以「命令失败」退出。不要留下 `logs/.<app>.sync.stdout` 这类文件，也不要把 `Start-Process` 的原始错误留成未处理异常。

启动分三段：先停命令行核对得上的本应用进程；端口上还有其他 PID 就列出并失败，不杀它们；60 秒内在启动器子孙里找到恰好一个应用进程，排除启动器自身。探测到端口后的等待与 6.5 第 3 段相同，默认 180 秒。进程在监听前退出就删掉 PID 文件并失败。没有探测到端口则跳过端口等待。

Java `run` 用全限定主类名。`jar` 用 `target/<finalName>.jar`，工作目录按启动目录核对。Node 用 `APP_CMD_MARKER`；Vite 填 `vite/bin/vite`。包装进程只算启动器。

停止使用 `Stop-Process -Id`。等待使用 `Wait-Process -Id -Timeout 25`。超时后只对这个 ID 执行 `Stop-Process -Id -Force`。停完再扫一次，仍有匹配进程就列出 PID 并失败。父进程只沿本次的 pnpm、npm 或 yarn 上溯；Java 启动器仍按 mvn、gradle、classworlds 核对。遇到 PID 0、PID 4，或不属于该应用，就停止上溯。

已设置且主版本符合的 `JAVA_HOME` 直接使用，不用更高版本替换。找不到要求的 JDK 就失败，并提示写到 `config/<app>.env`。example 只写占位符，口令类用 `change-me`，加载时跳过空值和 `change-me`。

和 bash 的差别只有这些：

- 用 `Win32_Process` 的 `CommandLine` 和 `ParentProcessId` 识别进程。能可靠读到工作目录时再核对工作目录。读不到就不要编一个路径，也不要单凭缺工作目录判成不匹配；读到了就必须和工作目录规则一致。
- 监听端口用 `Get-NetTCPConnection` 按本地端口读取，不要只加 `-State Listen`。`State` 为 `Listen` 算监听。IPv6 `::` 上有些监听记录的 `State` 是 0 或空，远端端口仍是 0，也算监听。远端端口不是 0 的已建立连接不算。读到监听但没有可用 PID 时失败，不要杀进程。
- 新进程用 `Start-Process -PassThru` 启动，记下返回的进程 ID。标准输出和标准错误追加到 `logs/<app>.log`。`.cmd` 由系统启动，返回的进程 ID 仍是这次 `Start-Process` 的结果。
- 失败摘要按 UTF-8 读 `logs/<app>.log`，打开时使用 `FileShare.ReadWrite`，日志泵占着文件也能读。读失败只写一行说明，然后继续原来的失败退出。进程刚退出时先等日志泵结束，最多 1 秒。控制台按 UTF-8 写，不沿用代码页 936。
- 启动 Java 时把 `stdout.encoding`、`stderr.encoding`、`sun.stdout.encoding`、`sun.stderr.encoding` 设为 UTF-8。`jar` 写在 `java` 命令里、`-jar` 之前。`run` 写进 `JAVA_TOOL_OPTIONS`，让 Maven 或 Gradle 拉起的 JVM 继承。这样 `System.out` 不再按代码页 936 写入日志。
- JDK 只查已设置的 `JAVA_HOME`、当前 `java`，以及 Program Files 下的 Java、Eclipse Adoptium 这类安装目录。不要写死某一台机器的用户目录。

## 7. 生成前复查

- [ ] 只写了 `scripts/runtime/<os>/`，且 `<os>` 是本次目标系统
- [ ] 脚本基名来自 `spring.application.name` 或 Node 包名
- [ ] 未被根 `dev` / `start` 引用的包没有脚本
- [ ] Java 默认是 `spring-boot:run` 或 `bootRun`，`jar` 才 `package -DskipTests` 或 `bootJar`
- [ ] `run` 模式写了 `run/<app>.pid` 与 `run/<app>.launcher.pid`
- [ ] 没有 `killall`、`pkill`、`taskkill /IM java`
- [ ] 没有修改项目原配置
- [ ] example 中没有真实口令
- [ ] `macos` 的 `lib/common.sh` 与 `templates/macos/common.sh` 一致，没有改写
- [ ] `linux` 的 `lib/common.sh` 与 `templates/linux/common.sh` 一致，没有改写
- [ ] `windows` 的 `lib/common.ps1` 与 `templates/windows/common.ps1` 一致，没有改写
- [ ] `windows` 的三个汇总脚本在每次 `&` 之后检查 `$LASTEXITCODE`，只有非 0 才退出
- [ ] `windows` 优先启动 `.exe` / `.cmd`；只有 `.ps1` 时用 `powershell.exe -File`。失败摘要是 UTF-8，旁路文件已删除
