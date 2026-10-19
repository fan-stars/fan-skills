---
name: f-yudao-boot-mini-graalvm
description: >-
  在 yudao-boot-mini（JDK25 + Spring Boot 4）上按增量阶段做 GraalVM Native Image。
  触发词：graalvm、native-image、native:compile、-Pnative、jdk25-graalvm、
  `native/test/first` (原 jdk25-graalvm-temp)、AOT、RuntimeHints、reachability metadata。编排已安装的
  java-add-graalvm-native-image-support 与 oracle graal，不参考旧 master-native。
---

# yudao-boot-mini GraalVM Native（JDK25 / Boot4）

## 何时使用

- 在试验支 **``native/test/first` (原 jdk25-graalvm-temp)`** 上拆模块做 native 打包与死磕
- 自 `jdk25-fan` 新建正式支 **`jdk25-graalvm`** 并只叠加白名单 Native 配置
- 增量开启模块后反复 `native:compile` / 排障
- 需要 RuntimeHints、tracing agent、reachability metadata

## Skill 编排（必读顺序）

1. **本 skill**：项目约束、阶段、裁剪规则（优先）
2. **`java-add-graalvm-native-image-support`**：Spring Boot 接入、迭代修错、RuntimeHints 模式  
   路径：`.agents/skills/java-add-graalvm-native-image-support/SKILL.md`
3. **`graal`（Oracle）**：Maven Native Build Tools、metadata、排障路由  
   路径：`.agents/skills/graal/SKILL.md` → 按需打开 `native-image/*.md`

冲突时：**本 skill 的项目约定 > awesome-copilot 通用模板 > oracle 示例版本号**。

权威双分支策略：工作区 `docs/native/native-dual-branch-strategy.md`；OpenSpec：`add-native-dual-branch-jdk25`。

## 硬约束

- 功能基线：`jdk25-fan`
- 试验支：``native/test/first` (原 jdk25-graalvm-temp)`（永不合 fan / 正式支）
- 正式支：自 fan 新建 `jdk25-graalvm`（白名单叠加；最终合 fan，按变更授权择机）
- **禁止**参考 / cherry-pick `master-native`（旧 JDK / Boot3 路线）
- **禁止**将 temp merge / cherry-pick 到其他交付分支
- 工具链：
  - `JAVA_HOME=/root/devenvi/graalvm-community-25.3.4.1+1.1`
  - Maven：`/root/devenvi/apache-maven-3.9.16`
  - 普通 JDK（非 native 编译）：`/root/devenvi/jdk-25.0.4+6` 可选
- `native-maven-plugin` 版本跟 **Spring Boot BOM**（Boot 4.1.x 为 `1.1.x`，如 4.1.1 → `1.1.8`），**不要**照抄 skill 示例里的 `0.10.x` / `0.11.1`
- 根聚合 POM：`skipNative=true`；仅 `yudao-server` 在 `-Pnative` 下构建
- 只 `native:compile` / AOT；不 merge 无关历史

## 裁剪原则（「关掉全部功能」）

当前默认 `yudao-server` 依赖 `system` + `infra` 即全量。真正空壳要：

1. **Maven**：server 暂时不依赖 `yudao-module-system` / `yudao-module-infra` / 可选 `protection`
2. **扫描**：临时收窄到 `*.server`，或只放 server 包内 Hello 接口
3. **不要**仅靠 yaml `enabled=false`（依赖仍在 classpath，native 仍会分析）

`system` 硬依赖 `infra`：恢复业务时优先「瘦 infra / stub API」，勿一次开全量 infra。

## 增量阶段（单变量；每阶段：JVM 通 → native 编过 → native 冒烟 → commit）

| Phase | 内容 | 成功标准 |
|-------|------|----------|
| 0 | server 空壳 + web（可先无 Knife4j）+ `/native/ping` + `-Pnative` | native 起进程，HTTP 200 |
| 1 | security | native 启动；安全链不炸 |
| 2 | mybatis 最小（仅 MySQL；评估关掉 dynamic-datasource / join / easy-trans） | native 能查一表 |
| 3 | redis（Redisson 卡则降级/后置） | native 读写缓存 |
| 4 | 最小 system（auth/user）；infra 仅必要 API | 登录或鉴权可用 |
| 5 | tenant / data-permission | 拦截器在 native 下工作 |
| 6 | infra 能力逐项：config → 本地文件 → monitor → ws → job → mq → excel；**排除 codegen/Admin/多协议文件客户端** 或标 JVM-only |
| 7 | captcha / mail / JustAuth / wx-java（单开） | 各阶段独立通过 |
| 8 | protection / lock4j | 限流幂等可用 |

失败只回退本阶段依赖，不进入下一阶段。

## 构建命令模板

```bash
export JAVA_HOME=/root/devenvi/graalvm-community-25.3.4.1+1.1
export PATH="$JAVA_HOME/bin:/root/devenvi/apache-maven-3.9.16/bin:$PATH"
cd yudao-boot-mini

# JVM
mvn -pl yudao-server -am -DskipTests package

# Native（Boot4：先 AOT 再 native；以实际 profile 为准）
mvn -pl yudao-server -am -Pnative -DskipTests native:compile
```

排障顺序（对齐 oracle `graal`）：

1. `graal/native-image/troubleshooting.md`
2. 缺反射/资源/代理 → `reachability-metadata.md` 或 Spring `RuntimeHints`
3. 优先 tracing agent 收集，再手写 JSON：
   `java -agentlib:native-image-agent=config-output-dir=... -jar ...`
4. metadata 建议目录：`META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`

## Spring Boot 专用（awesome-copilot）

- 使用 `process-aot`；native 构建不要依赖未展开的 fat jar `BOOT-INF` 当唯一 classpath
- Logback：`logging.register-shutdown-hook=false`（native）
- 自定义 DTO / Hutool 反射 / Knife4j `Class.forName` → RuntimeHints 或 agent 元数据
- `--no-fallback`；OOM 时 `-J-Xmx8g`（或更大）

## 明确不做

- 不一次打开 system+infra 全依赖再指望 native 一次过
- 不把 Quarkus/Micronaut 注解模式套到本项目
- 不修改仓库内业务配置密钥；本地配置走仓库外约定（见 `f-java-springboot`）
