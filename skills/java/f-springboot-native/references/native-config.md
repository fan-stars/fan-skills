# Native 配置与构建

优先 RuntimeHints；仅在其不适合或第三方格式明确要求时使用 `src/main/resources/META-INF/native-image/` 下的 `reflect-config.json`、`resource-config.json`、`proxy-config.json`、`serialization-config.json`、`jni-config.json`。

每个配置文件必须对应具体错误或无法表达的元数据，禁止全包、全资源目录和无理由 workaround。已有依赖 Metadata 时删除项目副本。

Maven/Gradle DSL、Native task/profile 与参数必须从项目文件和实际插件版本确认。只添加必要参数；初始化参数必须限定到已定位的类。

没有 GraalVM、Native toolchain、Docker 或所需外部服务时，不假设对应构建/集成测试可执行；明确标为“未执行”并给出可复现命令。目标 OS、架构和 libc 与构建环境不一致时，单独报告平台风险。
