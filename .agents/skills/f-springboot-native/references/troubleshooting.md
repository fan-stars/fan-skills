# Native 错误定位

先保留完整错误、Native 命令、版本和最小复现。按类别处理：

- AOT：检查生成的 AOT 代码和 Spring 版本支持。
- Reflection：定位 Class 与具体 member，查官方 Metadata，再用最窄 RuntimeHints。
- Resource：定位 classpath 路径，添加窄资源 hint。
- Proxy：区分 Spring 代理与自建 JDK Proxy，先修 AOT 覆盖。
- Serialization/SPI/JNI：确认真实运行路径、配置文件或 native library。
- Initialization：只对报错 Class 解释 build-time/run-time 原因后调整。
- 第三方依赖：查其版本和官方 Reachability Metadata；不要重复注册。

每次修复后先重跑失败测试，再跑 JVM 基线和 Native 启动/API/核心业务验证。不要用 `--allow-incomplete-classpath` 或大范围配置隐藏错误。

排查前清理旧的 `target/`、`build/`、AOT 输出和 Native executable，确认不是缓存污染。记录目标 OS/CPU/libc、构建方式（本机或容器）、外部依赖和工具链版本；将环境不可用与代码失败分开报告。瘦身或删除配置时保留可回滚的有效基线。
