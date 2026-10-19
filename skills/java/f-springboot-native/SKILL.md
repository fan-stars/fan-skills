---
name: f-springboot-native
description: Audit, diagnose, and minimally adapt existing Java Spring Boot projects for GraalVM Native Image while preserving business code, behavior, and architecture.
metadata:
  short-description: Spring Boot Native Image audit and minimal adaptation
---

# Spring Boot Native Image 审计与改造

这是一个 **Spring Boot Native Image 审计与改造 Skill**，不是 Java 代码重构或架构重设计 Skill。目标是在最大程度保持现有业务代码、逻辑和架构不变的前提下，使现有 Spring Boot（包括 Spring Boot 4 / JDK 25）项目可靠支持 GraalVM Native Image。

## 不可违背的边界

- 默认 `NO BUSINESS CODE CHANGE`：不主动重构 Controller、Service、Repository、Domain、Entity、DTO、Mapper、API、数据库、事务、权限或业务流程。
- 不为 Native 把动态代码全部静态化，不改变业务逻辑，不更换框架或第三方依赖；只有用户明确要求或所有元数据方案都无法表达行为时才提出这些变更。
- 优先新增配置、RuntimeHints、Native 注解、`META-INF/native-image` 配置、构建配置和测试；任何业务代码变更都必须先报告文件、原因、为何配置不能解决及行为影响。
- 不用大范围 reflection/resource/proxy、`--allow-incomplete-classpath`、unsafe 或无理由初始化参数掩盖问题。
- 配置语义和第三方业务调用逻辑也属于保护范围；不得为了 Native 做代码风格重构。

核心理念：Spring Boot Native 改造是在现有 JVM 应用之上补充 Native Runtime Metadata。配置不是越多越好，而是越少越好；JVM 与 Native 必须保持行为一致。

## 解决顺序（AOT First）

按以下优先级判断并实施，每一步都避免重复覆盖前一步已经解决的内容：

1. Spring Boot AOT
2. Spring Framework AOT
3. 第三方库官方 Native / Reachability Metadata
4. `RuntimeHints` / `RuntimeHintsRegistrar`
5. `src/main/resources/META-INF/native-image/` 中精确的配置文件
6. Native build 参数
7. 最后才考虑业务代码修改

涉及 API 时先读取项目实际 Spring Boot / Spring Framework 版本和官方文档；不要把 Boot 3 的旧 API 套到 Boot 4。`@ImportRuntimeHints` 或等价机制必须以实际版本为准。

## 注解与 RuntimeHints 选择

若当前 Spring Boot / Framework 版本提供适用的 Native Hint 注解，且只声明元数据、不改变业务流程，应优先考虑注解；AOT 已能识别时不添加重复注解。对项目自身无法由 AOT 推导的动态行为，优先使用 `RuntimeHintsRegistrar`。每一条 hint 或注解都要记录代码位置、触发路径、最小权限和对应测试。

## 工作模式

### Native Audit

只读分析，不修改任何文件；即使发现可修复项也只提出建议。输出兼容性结论、风险清单、AOT 可处理项、RuntimeHints/资源/代理/反射候选、第三方依赖与初始化风险、必须修改项和可选优化项。

### Native Prepare

仅在用户明确要求改造时，以最小侵入完成改造：先建立 JVM 基线，再添加必要的 AOT 配置、RuntimeHints、Native 配置、构建配置和测试。默认不改业务实现、API、数据库、架构或技术栈。

### Native Fix

仅在用户明确要求修复时，针对 compile、startup 或 runtime 错误，依次定位具体 Class/Resource/Method，判断 AOT、第三方 Metadata、RuntimeHints、配置文件和初始化策略是否可解决，最后才考虑业务代码。禁止直接堆 GraalVM 参数。

### Native Verify

验证 AOT、Maven/Gradle Native 构建、Native 启动，以及 API、数据库、Redis、MQ、资源、序列化、反射、代理和核心业务测试；同时确认 JVM 模式仍可运行。

详细检查表见 [references/audit.md](references/audit.md)，错误处理见 [references/troubleshooting.md](references/troubleshooting.md)。

Audit 允许在 JVM 基线失败时继续做静态审计，但必须把基线失败单独记录，不能归因于 Native；在基线未恢复前，Native 结论标记为“受限验证”。所有结论标注证据：`已源码确认`、`已构建确认`、`已运行确认` 或 `待验证`。

## 标准分析流程

1. 识别 Spring Boot、JDK、Maven/Gradle、GraalVM、Native Build Tools 和模块结构。
2. 读取 `pom.xml`/`build.gradle*`，识别主要第三方依赖及其官方 Native Metadata。
3. 检查 `src/main/java`、`src/main/resources` 和现有 Native 配置。
4. 审计 `Class.forName`、`ClassLoader.loadClass`、反射成员调用、`Proxy.newProxyInstance`、`ServiceLoader`、动态字节码、JNI、Agent、脚本和模板引擎；扫描 `getResource`、`getResourceAsStream`、`ClassPathResource`、`ResourceLoader`、`ResourcePatternResolver`。
5. 盘点 `templates`、`static`、`mapper`、`i18n`、XML/JSON/YAML/properties、HTML/FTL/Mustache、PEM/CER/TXT、字体、时区/Locale 数据、GraphQL/Proto、证书和 `.so/.dll/.dylib` 等 classpath resource。
6. 先标记 AOT 已能推导的内容；仅对剩余问题设计最小 RuntimeHints。
7. RuntimeHints 不适合时才使用 `META-INF/native-image`；每个文件和条目都要有具体原因。
8. 仅在真实错误且定位到具体 Class 时调整 build-time/run-time initialization。
9. 根据实际 build 文件确认命令；不要假设 profile、task 或插件存在。
10. 改动后重新审计重复配置、过度注册、第三方 Metadata 重复维护和不必要业务变更。
11. Native 构建前确认目标 OS、CPU 架构、glibc/musl、容器/本机构建方式及动态库；清理 `target/`/`build/`、AOT 输出和旧 executable 后再复现关键结果，避免缓存污染。

## 元数据规则

- Reflection：精确到 Class 和 `MemberCategory`；只注册所需 fields/constructors/methods，禁止全包或全项目注册。
- Resource：优先 `hints.resources().registerPattern()`，只开放无法由 AOT 识别的路径，避免全目录。
- Proxy：区分 Spring AOP、Spring Framework、第三方和项目自建 JDK Proxy；Spring 相关优先交给 AOT，剩余才使用 `hints.proxies()`。
- Serialization：先 AOT，再 RuntimeHints，最后才是 `serialization-config.json`；单独检查 Java Serialization、Jackson 特殊场景和第三方序列化。
- SPI：检查 `ServiceLoader` 与 `META-INF/services`；第三方优先复用官方 Metadata，项目自有 SPI 尽量用 RuntimeHints 或 Spring 机制。
- 第三方依赖：重点核查 MVC/WebFlux、Security、Jackson、Validation、MyBatis/Hibernate/JPA、Redis、Kafka/MQ、Netty、ES/Mongo、AWS/MinIO、POI/PDF/图片/XML/模板/RPC/JNI/脚本等。已有官方 Metadata 时不得重复维护。
- 初始化：不默认添加 `--initialize-at-build-time` 或 `--initialize-at-run-time`；先解释具体类为何失败，再给最窄范围参数。

RuntimeHints 示例只作为版本校准后的形状参考：

```java
final class NativeRuntimeHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // 仅注册已证明且无法由 AOT 推导的类型、资源或代理
    }
}
```

## 基线、构建与验证

条件允许时先运行 `./mvnw test` 或 `./gradlew test`，区分既有失败与 Native 问题。Maven 优先使用项目现有 `spring-boot-maven-plugin` 与 `org.graalvm.buildtools:native-maven-plugin`；Gradle 检查 `org.graalvm.buildtools.native` 插件及实际 DSL。Native 命令必须从实际构建文件确认，例如项目确实提供时才使用 `./mvnw spring-boot:run`、`./mvnw -Pnative native:compile`、对应 `nativeCompile` 或 Native `bootBuildImage`。

验证顺序为 JVM 构建/测试 → AOT → Native compile → 可执行文件启动 → API/Context → 数据库、Redis、MQ、配置和资源 → 序列化、反射、代理及核心业务集成测试；最终确认 JVM 与 Native 都可运行。

## 固定输出格式

Native Audit / Prepare / Fix 完成后输出：

```text
# Native 改造报告
## 1. Native 改造总结
兼容程度、AOT 覆盖、RuntimeHints 数量、Native 配置文件、业务代码修改结论
## 2. 项目环境
Spring Boot / JDK / Build Tool / GraalVM / Native Build Tools
## 3. 修改文件清单
新增/修改文件；明确列出未修改的业务目录
## 4. AOT 可以自动处理
...
## 5. RuntimeHints
完整代码或精确变更；没有则明确说明
## 6. Native 配置文件
完整内容或精确变更；没有则明确说明
## 7. Maven / Gradle 配置
完整修改和实际命令
## 8. 必须修改业务代码
无则写“无需修改业务代码”。有则逐项给出原代码、修改后代码、Native/AOT/Hints/配置为何不能解决、业务影响及 JVM/Native 一致性
## 9. Native 风险清单
高 / 中 / 低；包含第三方依赖风险和处理方式
## 10. 验证方案
JVM 测试、AOT、Native compile、Native 启动、Native integration test 及结果
```

Native Verify 还要单独列出每个阶段的 `通过 / 失败 / 未执行 / 受限`，并说明外部依赖（数据库、Redis、MQ、Testcontainers 或本地服务）是否可用、失败是否由环境造成。

## 可直接复用的提示词

- **完整 Native 审计**：分析当前 Spring Boot 项目 Native 兼容性；不改业务代码，检查 AOT、Reflection、Resource、Proxy、SPI、Serialization、JNI、初始化和第三方依赖，只找真正需要配置的地方。
- **Native 配置最小化审计**：审计所有 RuntimeHints、`*-config.json` 和 Native build arguments，删除 AOT 已处理、第三方已提供、重复或过度配置，说明删除/保留项与风险。
- **Native 业务代码零侵入审计**：检查为 Native 修改的 Controller/Service/Repository/Domain/Entity/DTO/Mapper，评估能否以 AOT、RuntimeHints 或 Metadata 恢复原代码。
- **Reflection 审计**：只审计反射和动态加载，按 AOT → 官方 Metadata → RuntimeHints → Native Config 顺序提出精确方案。
- **Third-party Native 审计**：输出 Dependency、Native Support、AOT Support、Official Metadata、Required Hints、Risk，禁止重复实现官方 Metadata。
- **Native Error Fix**：定位错误 Class/代码，依次分析 AOT、Metadata、RuntimeHints、Resource/Proxy/Initialization，给出最小修复。
- **Native 配置瘦身**：删除无用 Reflection、重复 Resource/Proxy/Metadata、无必要初始化和 GraalVM 参数，输出删除项、保留项、原因和风险。

参考：
- [references/audit.md](references/audit.md) — 审计字段和证据要求
- [references/runtime-hints.md](references/runtime-hints.md) — RuntimeHints、反射、资源、代理和序列化的最小化规则
- [references/native-config.md](references/native-config.md) — `META-INF/native-image` 与构建参数选择
- [references/troubleshooting.md](references/troubleshooting.md) — Native 错误分类和定位顺序
