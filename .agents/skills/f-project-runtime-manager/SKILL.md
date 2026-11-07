---
name: f-project-runtime-manager
description: >-
  Generates start/stop/restart/status scripts for Java, Spring Boot, React,
  Next, Vue, Nuxt, and other Node apps. Use when the user asks for
  项目启动脚本 or mentions spring.application.name, macos, linux, windows,
  or scripts/runtime.
---

# Project Runtime Manager

按当前工作区的探测结果生成启停脚本。构建布局、模块名、包管理器、端口和 jar 路径都来自探测。单模块与多模块使用不同命令。示例里的名字是虚构的。

## 硬性约束

1. 先探测并展示清单。主入口集合明确后再写文件。集合不明确时停下来等用户指定。
2. 只在 `<workspace>/scripts/runtime/<os>/` 新增运行脚本。`<os>` 只能是 `macos`、`linux`、`windows`。
3. 默认只生成当前系统的目录。用户点名目标系统时只生成那一个目录，即使当前机器不是该系统。
4. 不修改项目自带的 `application*.yml`、`application*.yaml`、`bootstrap*`、`.env*`、`package.json`、`vite.config.*`、`nuxt.config.*`、`pom.xml`、`build.gradle*`、`settings.gradle*`。
5. 不修改 `scripts/runtime/` 以外的已有脚本。工作区根 `.gitignore` 只允许追加本技能规定的运行时忽略规则。
6. 脚本基名是项目名。不要用 `backend` 或 `frontend` 做前缀。
7. 真实 `config/<app>.env`、`run/`、`logs/` 不提交。`*.env.example` 和脚本可以提交。
8. 停进程只杀死记录下来、且命令行与工作目录都核对属于该应用的 PID。禁止 `killall`、`pkill`、`taskkill /IM java`，以及按进程名模糊匹配。
9. `macos` 与 `linux` 使用 `#!/usr/bin/env bash`，语法停在 bash 3.2：不用关联数组，不用 `${var,,}`，不依赖 `mapfile`。`windows` 使用 PowerShell 5.1 的 `.ps1`。
10. 已有脚本与本次探测不一致时，先展示差异，确认前不覆盖。已存在的 `config/<app>.env` 不覆盖。
11. 示例只使用虚构的目录名和项目名。生成脚本时写入本次探测结果，不要把示例名字写进目标项目。

## 工作流程

```text
Task Progress:
- [ ] 1. 确定工作区根与目标系统
- [ ] 2. 列出候选运行根
- [ ] 3. 确定主入口与脚本基名
- [ ] 4. 展示清单；不明确则等待
- [ ] 5. 生成 scripts/runtime/<os>/
- [ ] 6. 追加尚缺的 gitignore 规则
- [ ] 7. 语法检查与 status 空跑
- [ ] 8. 向用户交付清单与最短命令
```

### Step 1：工作区根与系统

工作区根是用户当前打开的工作区。单仓库时它就是仓库根。多仓库时脚本写在工作区根，不写进子仓库。

入口脚本从自身位置向上三级得到工作区根：`<workspace>/scripts/runtime/<os>/<name>.sh`。应用目录写成相对工作区根的路径。`lib/common.sh` 比入口脚本深一层，向上四级才是工作区根。

| 探测值 | 目录 |
| --- | --- |
| `Darwin` | `macos` |
| `Linux` | `linux` |
| `Windows_NT`、`MINGW*`、`MSYS*`、`CYGWIN*` | `windows` |

在 Mac 上为 Linux 服务器准备脚本时，必须由用户显式指定 `linux`。不要一次写出三套目录。

### Step 2：候选运行根

只检查工作区根，以及它的直接子目录。目录要直接含有 `pom.xml`、`build.gradle`、`build.gradle.kts` 或 `package.json`。跳过名为 `.tmp`、`generated`、`worktrees`、`.worktree`、`node_modules`、`dist`、`target` 的子目录。不向更深层递归寻找另一个项目根。直接子目录若被父构建文件的 Maven `<modules>` 或 Gradle `include` 列出，它不是另一个候选根。

有 `pom.xml` 时用 Maven。没有 `pom.xml` 且有 Gradle 构建文件时用 Gradle。

### Step 3：主入口与脚本基名

Java：统计带 `spring-boot-maven-plugin`、Gradle 插件 `org.springframework.boot` 或 `@SpringBootApplication` 的构建单元。恰好一个才生成。零个则不生成 Java 脚本。多于一个则列出路径并等待，不擅自挑选。

布局只在候选根上判断。可执行单元的构建文件就在候选根时，按单模块处理，命令在候选根执行。构建文件在该候选根的子目录时，按多模块处理，命令在候选根执行。不要把列在父模块清单里的子目录再当成单模块候选根。

Java 基名按顺序取第一个有值的结果：

1. 该模块 `src/main/resources/application.yaml`、`application.yml` 或 `application.properties` 里的 `spring.application.name`。
2. 该模块的 `artifactId`。
3. 该模块目录名。

基础文件已经有名字时，`application-<profile>.*` 不覆盖它。不要把 docker-compose 或命令行里的 `--spring.application.name` 当作脚本名。

Node：读候选根的根级 `package.json`。有 `scripts.dev` 就解析它，否则解析 `scripts.start`。解析出的包是唯一 Node 主入口。`dev:*`、`build`、`preview` 不额外增加应用。根上没有 `dev` 和 `start`，且只有一个子包有 `dev` 或 `start` 时，用那个子包。多个子包各自有 `dev` 时列出并等待。

从脚本文本识别包的写法见 [reference.md](reference.md)。包管理器按锁文件：`pnpm-lock.yaml`、`yarn.lock`、`package-lock.json`，然后 `packageManager` 字段，最后才是 npm。

Node 基名取该包 `package.json` 的 `name`，去掉 scope，折成小写 `[a-z0-9-]`。没有 `name` 时用所在文件夹名。两个应用折成同一个基名时，后面加上父目录名。

被 Step 3 选中的 Node 包只要有 `dev` 或 `start`，就生成同一套四动词脚本。依赖名只写进探测说明：`react`、`next`、`vue`、`nuxt`、`@angular/core`、`svelte`、`astro`、`express`、`fastify`、`koa`、`@nestjs/core`。对不上时写 Node。React、Next、Vue、Nuxt 因此共用这一套流程。

磁盘上存在、但没有被选中脚本引用的包，写进探测说明，不生成脚本。

### Step 4：清单

集合明确时，展示清单后继续生成。集合不明确时，展示候选后停止，不写文件。

### Step 5：生成

文件布局、`run` / `jar` 参数、PID 与停止算法见 [reference.md](reference.md)。单模块示意名是虚构的 `ledger`，前端示意名是 `shop-console`。根脚本没有引用的包，例如 `shop-mobile`，只写进探测说明，不生成脚本。多模块命令只写 `<module>`，不写死某一套父子目录。命令示意见 [examples.md](examples.md)。示例里的目录名、包名、端口和 jar 路径都是虚构的，必须换成本次探测结果。

生成 `macos` 时，把 [templates/macos/common.sh](templates/macos/common.sh) 原样复制为 `scripts/runtime/macos/lib/common.sh`。不要改写这份进程库。每个主入口另写 `lib/app-<app>.sh`，只放本次探测到的身份、端口变量和命令数组。入口脚本只负责定位工作区、source 这两个文件，并调用 `runtime_start`、`runtime_stop`、`runtime_restart` 或 `runtime_status`。linux 与 windows 的模板留到对应机器，本次不要新增。

每个主入口四份脚本：`<app>-start`、`<app>-stop`、`<app>-restart`、`<app>-status`。两个及以上主入口时再生成 `start-all`、`stop-all`、`status-all`。`start-all` 先启动 Java，再启动 Node。前一个失败则不再启动后面的。

Java 默认模式 `run` 不要先做 `package`。单模块在候选根执行 `mvn spring-boot:run`，或 `./gradlew bootRun`。多模块的 `run` 分两步，都在 reactor 根执行：先 `mvn -pl <module> -am -DskipTests install`，再只对可执行模块执行 `mvn -pl <module> org.springframework.boot:spring-boot-maven-plugin:<version>:run`，这一步不要加 `-am`。插件坐标和 `<version>` 的读法见 [reference.md](reference.md)。Gradle 多模块仍用 `./gradlew :<gradlePath>:bootRun`。第一个参数为 `jar` 时才打包再 `java -jar`。Node 脚本收到 `jar` 时退出码为 2，并打印用法。`node_modules` 不存在时先 install 一次，不在 dev 之前做生产构建。

配置写入 `scripts/runtime/<os>/config/<app>.env.example`，只放占位符。真实 env 不存在时从 example 复制，之后不覆盖。项目原来没有 `--spring.config.additional-location` 约定时，不另造 yaml。已有该约定时，沿用原来的文件名和参数，把文件放到这个 `config/` 目录。

### Step 6：gitignore

在工作区根 `.gitignore` 追加尚不存在的规则，已有规则保持原样：

```gitignore
scripts/runtime/*/config/*.env
!scripts/runtime/*/config/*.env.example
scripts/runtime/*/run/
scripts/runtime/*/logs/
```

### Step 7：校验与交付

- `macos` 与 `linux`：对每个生成的 `.sh` 执行 `bash -n`。
- 执行每个 `*-status` 脚本，确认它不启动进程。
- 向用户交付：目标系统、探测清单（含明确不生成的包）、新增文件、最短启动/停止/状态命令、配置路径。
- 明确声明：未修改项目既有配置与源文件。

## 再次生成

先读已有的 `scripts/runtime/<os>/`。文件不存在则创建。内容与本次探测一致则保持不动。内容不同则把 `diff -u` 展示给用户，确认前不覆盖。`config/<app>.env` 始终不覆盖。
