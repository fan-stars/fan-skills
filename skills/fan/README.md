# Fan 自研

Fan 团队自行编写、非来自公开开源项目的 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-base-project-initializer` | `skills/fan/f-base-project-initializer/` | 从固定 fan-base / fan-base-vben 模板克隆并重命名，生成可运行的 Fan 全栈新项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer/SKILL.md) |
| `f-base-project-initializer-cn` | `skills/fan/f-base-project-initializer-cn/` | 中文指引：从固定 fan-base / fan-base-vben 模板初始化并重命名 Fan 全栈项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer-cn/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/fan/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的隔离增量逆向、可查询证据索引与质量门禁技能。 | 暂无 | [本仓库](../../.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
| `f-java-springboot` | `skills/fan/f-java-springboot/` | Fan 后端 Spring Boot 硬性约定：MyBatis-Plus、Lombok 日志与仓库外本地配置。 | 暂无 | [本仓库](../../.agents/skills/f-java-springboot/SKILL.md) |
| `f-project-runtime-manager` | `skills/fan/f-project-runtime-manager/` | 探测 Java/Spring Boot 与 Vue/Vite 项目结构，生成可移植的启停/状态脚本，不改原文件。 | 暂无 | [本仓库](../../.agents/skills/f-project-runtime-manager/SKILL.md) |

## 详细介绍

### `f-base-project-initializer`

**路径**：`skills/fan/f-base-project-initializer/`

#### 核心能力

按用户项目名规范化为 kebab-case，派生前后端目录、Maven groupId 与数据库名；克隆两仓后改远程名为 fan-base、解除 upstream；批量迁移 pom 坐标与库名配置，保留 fan-server 模块与外部依赖；可衔接生成运行脚本与 AGENTS.md，并做启动验证。

#### 适用场景

基于 Fan 官方 Gitee 模板开新项目、批量改名与坐标迁移、初始化后希望一键生成启停脚本或确认前后端能启动时使用。

#### 主要覆盖内容

必需输入与命名派生、克隆重命名与远程策略、Maven/数据库迁移不变量、残留模板名检查、后端 clean-build、可选运行脚本与 AGENTS.md、启动验证清单。

#### 注意事项

目标目录非空禁止覆盖。未提供目标远程时不得推送。英文版与中文版流程一致，按对话语言选用。本 skill 为 Fan 本地自建，无 skills.sh / 公开 GitHub。

### `f-base-project-initializer-cn`

**路径**：`skills/fan/f-base-project-initializer-cn/`

#### 核心能力

确认并规范化项目名后派生目录与坐标；拉取两模板仓、重命名远程并解除上游；迁移全部受控 pom 与数据库相关配置，保留 fan-server 可执行模块；可选生成根目录运行脚本与 AGENTS.md，并启动验证可运行应用。

#### 适用场景

中文协作下从 Fan 模板开新仓、改前后端目录名与 Maven/库名、需要初始化后生成启停脚本或验证能否启动时使用。

#### 主要覆盖内容

名称确认、双仓克隆与远程策略、Maven 与数据库迁移、残留模板名处理、后端构建、可选脚本与 AGENTS.md、启动验证阶段清单。

#### 注意事项

与英文版 `f-base-project-initializer` 同源流程，按用户语言选用其一即可，勿同时执行两套。非空目标目录不得覆盖；无用户远程时不推送。Fan 本地自建 skill。

### `f-enterprise-source-reverse-engineering`

**路径**：`skills/fan/f-enterprise-source-reverse-engineering/`

#### 核心能力

按项目隔离构建源码、符号和业务三层持久索引，增量复用未变化文件，提取方法调用与反向调用、路由、表、接口完整证据链和业务规则，并通过实际文件哈希、符号路由范围、运行记录及十八项门禁阻止伪造或不完整分析冒充完成。

#### 适用场景

需要初始化或刷新两套 PHP 项目工作区、查询文件模块归属或方法调用者、追踪规则关联接口与表、复核过期证据、严格审计模块完整度，或依据已批准的双项目结论设计 Java 目标系统时使用。

#### 主要覆盖内容

覆盖 A/B 单一根目录和事实隔离、源码与解析结果增量缓存、多模块追加归属、路由至副作用的接口链、业务规则关联查询、真实哈希行号、项目内 STALE 传播、原子锁写入、JSON Schema、运行轨迹和失败关闭式质量门禁。

#### 注意事项

核心脚本使用 Python 标准库并兼容 Windows 与 Linux 路径和进程调用；Schema 与平台格式测试需安装测试依赖。PHP 解析保持保守候选精度，动态调用和复杂语法必须人工复核，缺少状态、并发或跨模块证据时只能保持部分完成。

### `f-java-springboot`

**路径**：`skills/fan/f-java-springboot/`

#### 核心能力

在通用 Spring Boot 实践上强制三项：数据层用 MyBatis-Plus（LambdaQueryWrapper、单表优先、少 XML）；日志用 Lombok `@Slf4j`；开发配置写仓库外并启动加载，禁止改 Git 内配置。

#### 适用场景

编写或修改 Fan 项目后端 Java 代码时启用；与上游 `java-springboot` 冲突时以本 skill 为准。

#### 主要覆盖内容

按领域分包、构造器注入、Mapper/`BaseMapper`、仓库外 application-local 加载方式、Maven/Gradle 与相关 starter 选择。

#### 注意事项

常规 CRUD 不要引入 JPA。勿把个人路径或密钥写进仓库内 yml。新增配置前先确认项目是否已有 `.fan-local-config` 约定。

### `f-project-runtime-manager`

**路径**：`skills/fan/f-project-runtime-manager/`

#### 核心能力

先分析仓库（构建工具、可执行模块、包管理器、dev/build 脚本、端口/profile 只读推断），再在 `scripts/` 下生成 start/stop/restart/status（多应用可聚合）脚本；配置外置到 `scripts/config/`，安全停进程（PID 优先，禁用 killall/pkill），启动前必编译。

#### 适用场景

用户要求生成项目启动管理脚本、本地启停管理器、前后端进程管理或统一启动脚本时使用，尤其是 Spring Boot + Vue 单仓或 monorepo。

#### 主要覆盖内容

管理根目录判定、后端/前端探测启发式、脚本文件布局与生成规则、dry-run 校验与完成时输出；细节见 reference.md 与 examples.md。

#### 注意事项

禁止使用固定模板或硬编码路径；禁止改动 application*.yml、package.json、pom.xml 等既有文件，仅新增 `scripts/`。幂等生成，再次运行先读已有脚本增量更新。Fan 本地自建 skill，无公开仓库。
