# Java

Spring Boot、Fan 后端与 Java 重构

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `f-java-springboot` | `skills/java/f-java-springboot/` | Fan 后端 Spring Boot 硬性约定：MyBatis-Plus、Lombok 日志与仓库外本地配置。 | 暂无 | [本仓库](../../.agents/skills/f-java-springboot/SKILL.md) |
| `java-refactoring-extract-method` | `skills/java/java-refactoring-extract-method/` | 按范例在 Java 中安全实施 Extract Method，理清意图与类型边界。 | [skills.sh](https://skills.sh/github/awesome-copilot/java-refactoring-extract-method) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/java-refactoring-extract-method/SKILL.md) |
| `java-springboot` | `skills/java/java-springboot/` | Spring Boot 应用通用最佳实践：结构、注入、配置、数据访问与测试。 | [skills.sh](https://skills.sh/github/awesome-copilot/java-springboot) | [GitHub](https://github.com/github/awesome-copilot/blob/main/skills/java-springboot/SKILL.md) |

## 详细介绍

### `f-java-springboot`

**路径**：`skills/java/f-java-springboot/`

#### 核心能力

在通用 Spring Boot 实践上强制三项：数据层用 MyBatis-Plus（LambdaQueryWrapper、单表优先、少 XML）；日志用 Lombok `@Slf4j`；开发配置写仓库外并启动加载，禁止改 Git 内配置。

#### 适用场景

编写或修改 Fan 项目后端 Java 代码时启用；与上游 `java-springboot` 冲突时以本 skill 为准。

#### 主要覆盖内容

按领域分包、构造器注入、Mapper/`BaseMapper`、仓库外 application-local 加载方式、Maven/Gradle 与相关 starter 选择。

#### 注意事项

常规 CRUD 不要引入 JPA。勿把个人路径或密钥写进仓库内 yml。新增配置前先确认项目是否已有 `.fan-local-config` 约定。

### `java-refactoring-extract-method`

**路径**：`skills/java/java-refactoring-extract-method/`

#### 核心能力

以专家重构视角演示如何把长方法拆成意图清晰的小方法，包括空值/非法 ID 校验抽取、命名改进与保持行为等价。

#### 适用场景

Java 方法过长、条件嵌套或重复逻辑需要提取方法，且希望对照前后示例做等价重构时使用。

#### 主要覆盖内容

多组 before/after 示例，强调可读命名、早期返回与类型封装（如用领域 ID 代替原始 int）。

#### 注意事项

示例是模式启发而非可粘贴业务代码。重构后应保持对外行为与测试通过，避免借机改需求。

### `java-springboot`

**路径**：`skills/java/java-springboot/`

#### 核心能力

指导用 starter 与按领域分包搭建项目，构造器注入、外部化配置与 Profiles、类型安全 `@ConfigurationProperties`、持久化与测试等惯用做法。

#### 适用场景

编写或评审通用 Spring Boot 应用、引入标准分层与配置管理、尚无 Fan 特殊约束时使用。

#### 主要覆盖内容

Maven/Gradle、组件注解、配置与密钥、常见 starter 选型及质量实践概要。

#### 注意事项

Fan 仓库优先遵循 `f-java-springboot`（MyBatis-Plus 与仓库外配置）。本 skill 偏通用 JPA/配置习惯，冲突时以项目定制 skill 为准。
