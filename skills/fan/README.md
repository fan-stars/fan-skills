# Fan 自研

Fan 团队自行编写、非来自公开开源项目的 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-antd-spacing-layout-governance` | `skills/fan/f-antd-spacing-layout-governance/` | Ant Design 项目间距与跨页布局契约治理。 | 暂无 | [本仓库](../../.agents/skills/f-antd-spacing-layout-governance/SKILL.md) |
| `f-base-project-initializer` | `skills/fan/f-base-project-initializer/` | 从固定 fan-base / fan-base-vben 模板克隆并重命名，生成可运行的 Fan 全栈新项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer/SKILL.md) |
| `f-base-project-initializer-cn` | `skills/fan/f-base-project-initializer-cn/` | 中文指引：从固定 fan-base / fan-base-vben 模板初始化并重命名 Fan 全栈项目。 | 暂无 | [本仓库](../../.agents/skills/f-base-project-initializer-cn/SKILL.md) |
| `f-enterprise-source-reverse-engineering` | `skills/fan/f-enterprise-source-reverse-engineering/` | 面向双 PHP 遗留系统的项目强隔离、增量证据索引、可恢复运行与失败关闭质量门禁技能。 | 暂无 | [本仓库](../../.agents/skills/f-enterprise-source-reverse-engineering/SKILL.md) |
| `f-git-origin-doc` | `skills/fan/f-git-origin-doc/` | 盘点工作区独立 Git 仓与软链并生成 .git-origin 文档。 | 暂无 | [本仓库](../../.agents/skills/f-git-origin-doc/SKILL.md) |
| `f-git-origin-pull` | `skills/fan/f-git-origin-pull/` | 按 .git-origin 机器块 clone/fetch 独立仓，不合并不切换分支。 | 暂无 | [本仓库](../../.agents/skills/f-git-origin-pull/SKILL.md) |
| `f-java-springboot` | `skills/fan/f-java-springboot/` | Fan 后端 Spring Boot 硬性约定：MyBatis-Plus、Lombok 日志与仓库外本地配置。 | 暂无 | [本仓库](../../.agents/skills/f-java-springboot/SKILL.md) |
| `f-openspec-profile-switch` | `skills/fan/f-openspec-profile-switch/` | 在 legacy 与 opsx 两套 OpenSpec 技能配置间切换。 | 暂无 | [本仓库](../../.agents/skills/f-openspec-profile-switch/SKILL.md) |
| `f-project-runtime-manager` | `skills/fan/f-project-runtime-manager/` | 探测 Java/Spring Boot 与 Vue/Vite 项目结构，生成可移植的启停/状态脚本，不改原文件。 | 暂无 | [本仓库](../../.agents/skills/f-project-runtime-manager/SKILL.md) |
| `f-site-rewrite-implement` | `skills/fan/f-site-rewrite-implement/` | 按既有脚手架推进站点重写实现与对照。。用于目录浏览与选型。 | 暂无 | [本仓库](../../.agents/skills/f-site-rewrite-implement/SKILL.md) |
| `f-site-rewrite-init` | `skills/fan/f-site-rewrite-init/` | 站点重写项目的脚手架与索引初始化。。用于目录浏览与选型。 | 暂无 | [本仓库](../../.agents/skills/f-site-rewrite-init/SKILL.md) |
| `f-skills-library-ingest` | `skills/fan/f-skills-library-ingest/` | 将散落的 Agent Skills 有选择地纳入分类目录库的通用入库流程。 | 暂无 | [本仓库](../../.agents/skills/f-skills-library-ingest/SKILL.md) |
| `f-springboot-native` | `skills/fan/f-springboot-native/` | Spring Boot 应用 GraalVM Native Image 落地指南。 | 暂无 | [本仓库](../../.agents/skills/f-springboot-native/SKILL.md) |
| `f-yudao-boot-mini-graalvm` | `skills/fan/f-yudao-boot-mini-graalvm/` | 芋道 boot-mini 场景下的 GraalVM 原生构建经验。 | 暂无 | [本仓库](../../.agents/skills/f-yudao-boot-mini-graalvm/SKILL.md) |
| `f-zjmf-addon-plugin` | `skills/fan/f-zjmf-addon-plugin/` | 魔方云/ZJMF 插件后台开发约定与约束。。用于目录浏览与选型。 | 暂无 | [本仓库](../../.agents/skills/f-zjmf-addon-plugin/SKILL.md) |

## 详细介绍

### `f-antd-spacing-layout-governance`

**路径**：`skills/fan/f-antd-spacing-layout-governance/`

#### 核心能力

提供审计规则、迁移策略、扫描脚本与容器模板，统一间距语义。并给出可执行的步骤与约束说明。

#### 适用场景

Ant Design 6 项目出现间距混乱、迁移或 PR 审计时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 token 规则、gap/margin、响应式与页面契约。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

先定布局契约再改组件，避免只调像素不改结构。与用户显式指令冲突时以用户指令为准。

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

按 Project 绑定不同源码根并构建源码、符号和业务三层持久索引；通过完整限定参数类型、调用可达性与已知表关联生成结构事实，把 Service、Repository、Model、Request 等名称信号限制为候选；支持工作区内的外部权威 SQL 快照、带审核人和时间戳的负向证据安全写入、可信快照、失败阶段续跑、补证后独立终结，以及文件归属、方法调用者和业务规则关联接口与表查询。

#### 适用场景

适用于初始化或刷新两套大型 PHP 项目工作区、引用源码根外的权威数据库 dump、逐模块增量逆向、从失败阶段继续分析、为 PARTIAL 运行补齐人工证据后安全终结、查询文件归属或方法调用者、追踪规则关联接口与表、传播并复核过期证据、审计模块完成度，或依据已批准的双项目事实设计可追溯 Java 目标系统。

#### 主要覆盖内容

覆盖 A/B 根目录和事实读取隔离、源码与解析结果增量缓存、外部 SQL 的工作区边界及真实文件哈希行号校验、解析器版本失效、多模块追加归属及显式角色替换、路由到 Controller、验证、Service、持久化、事务和副作用的接口证据链、PRESENT 与 UNRESOLVED 及经审核的 NOT_APPLICABLE、STALE 传播、门禁候选与最终提交分离、完整自动管线及门禁尝试记录、JSON Schema 和十八项门禁。

#### 注意事项

核心脚本仅依赖 Python 标准库并兼容 Windows 与 Linux，Schema 和平台格式测试需安装测试依赖。外部 SQL 必须位于分析工作区内，不能用范围标记绕过文件存在、SHA-256、扩展名和行号检查；源码可信快照也不豁免这些检查。独立门禁只产生候选结果，补证后必须使用同一运行 ID 的 --finalize 完成最终提交。PHP 解析仍是保守候选解析，动态调用、复杂语法、非 HTTP 入口及是否真正不适用仍需人工补证。

### `f-git-origin-doc`

**路径**：`skills/fan/f-git-origin-doc/`

#### 核心能力

覆盖写入含 YAML 机器块的 README，供后续拉取技能消费。并给出可执行的步骤与约束说明。

#### 适用场景

新建工作区、子仓变更或需要远程来源盘点时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖仓发现、祖先 gitlink、软链与契约字段。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

默认不改根 .gitignore；不记录 commit hash。与用户显式指令冲突时以用户指令为准。

### `f-git-origin-pull`

**路径**：`skills/fan/f-git-origin-pull/`

#### 核心能力

缺失则克隆，已有则补 remote 并 fetch；远程 URL 冲突则停等确认。

#### 适用场景

按文档恢复工作区子仓或同步远程时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖解析 manifest、remote 冲突策略与软链跳过规则。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

禁止 merge/rebase/pull/checkout；软链需人工确保。与用户显式指令冲突时以用户指令为准。

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

### `f-openspec-profile-switch`

**路径**：`skills/fan/f-openspec-profile-switch/`

#### 核心能力

通过中央 vault 停放/投影 skills 与 commands，并同步仓库 spec 根。

#### 适用场景

需要从旧 OpenSpec 技能切到 /opsx 套件或反向时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 init/switch/specs-only、ACTIVE 与投影根。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

默认 dry-run；--apply 后建议重启 Agent 会话。与用户显式指令冲突时以用户指令为准。

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

### `f-site-rewrite-implement`

**路径**：`skills/fan/f-site-rewrite-implement/`

#### 核心能力

用观察记录与匹配量规驱动模块级重写，保持可追溯。并给出可执行的步骤与约束说明。并给出可执行的步骤与约束说明。

#### 适用场景

init 完成后逐模块迁移页面/数据时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 observation、match rubric 与实现节奏。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

对照未记录清楚时不要宣称模块完成。与用户显式指令冲突时以用户指令为准。与用户显式指令冲突时以用户指令为准。

### `f-site-rewrite-init`

**路径**：`skills/fan/f-site-rewrite-init/`

#### 核心能力

生成观察/对照/配置骨架，建立可续写的重写工作区。并给出可执行的步骤与约束说明。

#### 适用场景

开始从旧站到新站的系统重写时使用。也可在用户明确点名该技能时启用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖配置模板、indexes 与 secrets 示例。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

先 init 再 implement；密钥只用本地 secrets，勿提交。与用户显式指令冲突时以用户指令为准。

### `f-skills-library-ingest`

**路径**：`skills/fan/f-skills-library-ingest/`

#### 核心能力

盘点多扫描根候选 skill，与目录库真相源做差集，确认后再拷贝并更新 catalog，可选写入 commands 占位，最后交给 sync 渲染。

#### 适用场景

新建或扩充 skills 目录库、全局与库内不一致、整理 OpenSpec/superpowers 分类，或用户要求 skills 入库整理时使用。

#### 主要覆盖内容

覆盖扫描根约定、黑名单、分类启发式、commands 嵌套占位、与 sync-skills-catalog 的衔接及常见错误纠正。

#### 注意事项

确认前不写盘；禁止手改 skills/ 派生产物；路径可移植，不绑死单机。与用户显式指令冲突时以用户为准。

### `f-springboot-native`

**路径**：`skills/fan/f-springboot-native/`

#### 核心能力

覆盖原生配置、RuntimeHints、审计与排障，帮助可启动原生镜像。并给出可执行的步骤与约束说明。

#### 适用场景

要把 Boot 服务打成 native 或排查原生启动失败时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖 native-config、hints 与 troubleshooting 参考。

#### 注意事项

先保证 JVM 模式测试通过，再迭代原生可达性元数据。与用户显式指令冲突时以用户指令为准。

### `f-yudao-boot-mini-graalvm`

**路径**：`skills/fan/f-yudao-boot-mini-graalvm/`

#### 核心能力

针对 yudao-boot-mini 结构给出 native 构建与验证步骤。并给出可执行的步骤与约束说明。

#### 适用场景

在 fan 演示或 boot-mini 派生项目启用原生镜像时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖与该模板相关的构建注意点与验证。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

模板版本变化时先核对依赖与提示配置是否仍适用。与用户显式指令冲突时以用户指令为准。

### `f-zjmf-addon-plugin`

**路径**：`skills/fan/f-zjmf-addon-plugin/`

#### 核心能力

沉淀插件页面对齐、测试站操作与 Ant Design/Layui 边界等团队规则。

#### 适用场景

在 fan-zjmf 插件目录开发后台页或联调测试站时使用。也可在用户明确点名该技能时启用。

#### 主要覆盖内容

覆盖插件约束、UI 边界与常见操作注意点。细节以仓库内 SKILL.md 与引用文档为准。

#### 注意事项

仍用 Layui 的旧插件不要强行改成 Ant Design。与用户显式指令冲突时以用户指令为准。
