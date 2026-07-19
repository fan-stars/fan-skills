---

name: f-java-springboot
description: Fan 项目 Spring Boot 开发规范。基于 java-springboot 定制：数据层使用 MyBatis-Plus（优先 LambdaQueryWrapper、单表查询、少写 XML）；日志使用 Lombok @Slf4j；开发配置写入仓库外文件并在启动时加载，不修改 Git 仓库内配置文件。

---

# Fan Spring Boot 开发规范

在 Spring Boot 通用最佳实践基础上，遵循 Fan 项目的三项硬性约定：**MyBatis-Plus 数据访问**、**Lombok 日志**、**仓库外本地配置**。

编写或修改 Fan 后端 Java 代码时启用本 Skill；与上游 `java-springboot` 冲突时，**以本 Skill 为准**。

---

## 项目结构与依赖

- **构建工具**：Maven（`pom.xml`）或 Gradle（`build.gradle`）。
- **Starter**：`spring-boot-starter-web`、`mybatis-plus-boot-starter` 等；**不要**为常规 CRUD 引入 `spring-boot-starter-data-jpa`。
- **包结构**：按**功能/领域**分包（如 `com.fan.app.order`、`com.fan.app.user`），不按 controller/service/mapper 层分包。

---



## 依赖注入与组件

- **构造器注入**：必须依赖一律通过构造器注入，字段声明为 `private final`。
- **组件注解**：`@Service`、`@RestController`、`@Component`；数据访问接口使用 MyBatis-Plus 的 `BaseMapper`，**不要**使用 `@Repository` 标注 Mapper（MyBatis 用 `@Mapper`）。

---



## 配置（仓库外本地配置 — 强制）

开发过程中**禁止**修改 Git 仓库内的配置文件（如 `src/main/resources/application.yml`、`application-dev.yml`、`application-local.yml` 等已纳入版本库的文件）。

### 原则


| 场景                     | 做法                                        |
| ---------------------- | ----------------------------------------- |
| 新增/修改数据库、Redis、端口等开发配置 | 只改**仓库外**配置文件                             |
| 提交代码                   | 仓库内 `application*.yml` 保持团队基线，不含个人机器路径或密钥 |
| 启动应用                   | 额外加载仓库外配置，覆盖或补充仓库内默认值                     |




### 推荐目录

在**项目仓库同级或上级**维护本地配置目录，例如：

```
<workspace>/
  fan-xxx-server/          # Git 仓库
  .fan-local-config/         # 不纳入 Git（或加入全局 .gitignore）
    fan-xxx-server/
      application-local.yml
```

路径因项目而异；以各项目 README 或 `.fan-local-config` 约定为准。Agent 新增配置前应先确认项目是否已有该目录约定。

### 加载方式（任选其一，与项目既有方式一致）

**方式 A —** `spring.config.additional-location`**（推荐）**

仓库内 `application.yml` 仅保留占位或文档说明，例如：

```yaml
spring:
  config:
    additional-location: optional:file:${FAN_LOCAL_CONFIG:../.fan-local-config/fan-xxx-server}/
```

启动前设置环境变量 `FAN_LOCAL_CONFIG` 指向仓库外目录；未设置时使用相对路径默认值。

**方式 B — 启动参数**

```bash
java -jar app.jar --spring.config.additional-location=file:D:/devenvi/fan-config/fan-xxx-server/
```

**方式 C — IDE Run Configuration**

在 VM options 或 Program arguments 中追加 `spring.config.additional-location`，指向仓库外 YAML。

### Agent 操作清单

1. 需要改配置时 → 定位或创建**仓库外** `application-local.yml`（或项目约定的文件名）。
2. **不要** `git diff` 中出现对个人 `application-dev.yml` 的修改（除非用户明确要求改仓库内基线配置）。
3. 若仓库内缺少 `additional-location` 引导项，可向用户提议一次性添加**加载机制**（仍不把敏感值写入仓库）。



### 其他配置约定

- 类型安全绑定：继续使用 `@ConfigurationProperties`。
- 多环境：仓库内保留 `dev`/`prod` 结构；**个人开发差异**全部进仓库外 `application-local.yml`。
- 密钥：禁止硬编码；仓库外配置亦优先用环境变量引用（如 `${DB_PASSWORD}`）。

---



## Web 层（Controller）

- RESTful 风格、统一路径与 HTTP 动词。
- **DTO 与 VO 分离**：请求/响应使用 DTO/VO，**不要**把 `*DO` 实体直接暴露给前端。
- **校验**：JSR 380（`@Valid`、`@NotNull`、`@Size` 等）加在 DTO 上。
- **异常**：`@RestControllerAdvice` + `@ExceptionHandler` 统一错误体。

---



## Service 层

- 业务逻辑集中在 `@Service`；保持无状态。
- `@Transactional` 写在 Service 方法上，粒度尽量细。
- 跨表业务优先在 Service 内**多次单表查询**后组装，避免大而全的联表 SQL（见数据层）。

---



## 数据层（MyBatis-Plus — 强制）



### 总体原则

1. **使用 MyBatis-Plus**，不使用 Spring Data JPA / Hibernate 作为主要 ORM。
2. **尽量不写 XML**；`src/main/resources/mapper/*.xml` 仅在有充分理由时新增（复杂报表、数据库特有函数等），且需注释说明为何不能用 MP 表达。
3. **优先** `LambdaQueryWrapper` **/** `LambdaUpdateWrapper`，避免字符串列名硬编码。
4. **优先单表查询**；多表需求优先多次单表查询 + 内存组装，或 MP 的 `apply` 等简单条件，避免 JOIN 堆砌。



### Mapper

```java
@Mapper
public interface UserMapper extends BaseMapper<UserDO> {
    // 默认不写方法；复杂场景再按需增加
}
```

- 实体类命名 `*DO`，与表映射；使用 `@TableName`、`@TableId`、`@TableField`。
- 逻辑删除、自动填充（`createTime`/`updateTime`）使用 MP 全局配置或 `@TableLogic`、`MetaObjectHandler`。



### 查询示例（推荐）

```java
// 单表 + LambdaQueryWrapper
List<UserDO> list = userMapper.selectList(new LambdaQueryWrapper<UserDO>()
    .eq(UserDO::getStatus, status)
    .like(StringUtils.hasText(name), UserDO::getNickname, name)
    .orderByDesc(UserDO::getId)
);

// 分页
Page<UserDO> page = userMapper.selectPage(
    new Page<>(pageNo, pageSize),
    new LambdaQueryWrapper<UserDO>().eq(UserDO::getDeptId, deptId)
);
```



### 更新示例

```java
userMapper.update(null,
    Wrappers.<UserDO>lambdaUpdate()
        .set(UserDO::getStatus, newStatus)
        .eq(UserDO::getId, id)
);
```



### 避免


| 避免                   | 改用                      |
| -------------------- | ----------------------- |
| `QueryWrapper` 字符串列名 | `LambdaQueryWrapper`    |
| XML 中简单 CRUD         | `BaseMapper` 内置方法       |
| 多表 JOIN 查列表          | 单表查询 + Service 组装；或分步查询 |
| `@Select` 拼接易错 SQL   | `LambdaQueryWrapper` 链式条件 |
| JPA `JpaRepository`  | `BaseMapper<T>`         |




### 复杂查询决策

```
需要查数据？
  ├─ 单表条件过滤/分页 → LambdaQueryWrapper + BaseMapper
  ├─ 按 ID 批量补全关联名 → 先查主表，再 IN 查关联表（两次单表）
  ├─ 统计聚合简单 → MP selectMaps / selectObjs
  └─ 报表级复杂 SQL、存储过程 → 评估 XML 或 @Select，需说明理由
```

---



## 日志（Lombok — 强制）

- 使用 `@Slf4j`（Lombok），**不要**手写 `LoggerFactory.getLogger`。
- 使用占位符：`log.info("处理用户 userId={}", userId);`
- 异常记录：`log.error("操作失败, id={}", id, e);`（异常作为最后一个参数）。

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    // ...
}
```

确保模块已引入 Lombok 且注解处理器生效。

---



## 测试

- 单元测试：JUnit 5 + Mockito，Service 层 mock `Mapper`。
- 集成测试：`@SpringBootTest`；Mapper 层可用 `@MybatisPlusTest` 或带 Testcontainers 的真实库。
- 测试配置：可使用 `src/test/resources/application-test.yml`；**不要**把测试专用密钥写入仓库内主配置。

---



## 安全

- Spring Security、BCrypt 密码编码。
- 防 SQL 注入：依赖 MP 参数绑定，禁止拼接用户输入到 SQL 字符串。
- 输入校验与输出编码按 `security` Skill 与项目规范执行。

---



## 与 java-springboot 的差异摘要


| 主题   | java-springboot       | f-java-springboot              |
| ---- | --------------------- | ------------------------------ |
| 数据层  | Spring Data JPA       | MyBatis-Plus，Lambda，单表优先，少 XML |
| 日志   | `LoggerFactory`       | Lombok `@Slf4j`                |
| 开发配置 | 直接改 `application.yml` | 只改仓库外配置 + 启动加载                 |


