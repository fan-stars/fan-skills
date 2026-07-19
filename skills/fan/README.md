# Fan 自研

Fan 团队自行编写、非来自公开开源项目的 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-java-springboot` | `skills/fan/f-java-springboot/` | Fan 后端 Spring Boot 硬性约定：MyBatis-Plus、Lombok 日志与仓库外本地配置。 | 暂无 | [本仓库](../../.agents/skills/f-java-springboot/SKILL.md) |
| `f-project-runtime-manager` | `skills/fan/f-project-runtime-manager/` | 探测 Java/Spring Boot 与 Vue/Vite 项目结构，生成可移植的启停/状态脚本，不改原文件。 | 暂无 | [本仓库](../../.agents/skills/f-project-runtime-manager/SKILL.md) |

## 详细介绍

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
