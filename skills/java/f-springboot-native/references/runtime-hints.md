# RuntimeHints 最小化规则

先确认当前 Spring Framework API。使用 `RuntimeHintsRegistrar` 或当前版本推荐的导入机制；不要复制已废弃 API。

Reflection 必须精确到类型和 `MemberCategory`，只授予实际访问的成员。Resource 使用窄 pattern。Proxy 仅声明实际接口组合。Serialization 仅声明被 Native 运行路径证实的类型。每条 hint 写明对应调用路径和为何 AOT/官方 Metadata 无法覆盖。

完成后检查：是否可删除、是否与 AOT 或第三方 Metadata 重复、是否能用更窄类别/路径表达、JVM 与 Native 是否都通过。
