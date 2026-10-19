# Native Audit checklist

记录实际版本和证据：Boot、Framework、JDK、构建工具、GraalVM、Native Build Tools、模块。

审计项：

- 构建：插件、profile/task、AOT 任务、现有 Native 参数。
- 动态行为：反射 API、动态类加载、JDK Proxy、ServiceLoader、字节码、JNI、Agent、脚本。
- 资源：classpath 下 templates、static、mapper、i18n、XML/JSON/YAML/properties、证书及自定义路径。
- 运行时：序列化、初始化、网络客户端、数据库驱动、线程/代理。
- 依赖：查官方 Native/Reachability Metadata、Spring AOT 支持和版本限制。

依赖清单至少覆盖 Spring/MVC/WebFlux/Security、Jackson、Validation、MyBatis/Hibernate/JPA、Redis、Kafka/MQ、Netty、Quartz、Elasticsearch/MongoDB、MinIO/AWS、POI/PDF/Excel、XML/JSON、图片处理、加密、HTTP Client、RPC、SPI、JNI 和脚本引擎。对每项记录 Native 支持、AOT 支持、官方 Metadata、所需 Hints、风险和验证方式。

每个候选项记录：触发点、运行路径、AOT 是否覆盖、官方 Metadata 是否覆盖、最小修复、验证方式和残余风险。区分项目自有 Metadata、依赖包内 `META-INF/native-image`、Spring AOT 生成内容和项目自定义配置；不得把依赖 Metadata 复制到项目。没有运行证据时标为“待验证”，不要把猜测写成必须配置。

如果 JVM 基线失败，记录失败命令和原因，继续静态审计但将 Native 验证标记为“受限”。改造或瘦身时保留变更前基线，一次只删除/调整一类配置，验证失败则恢复最近一次有效状态。
