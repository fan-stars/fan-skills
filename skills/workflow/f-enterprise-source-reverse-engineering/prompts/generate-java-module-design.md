# 生成 Java 目标模块设计

基于 Project A/B 的 `${module}` 文档、比较报告、决策登记、新需求 `${requirements}`、相关模块摘要和全局 Java 约束 `${java_constraints}` 生成目标设计。

先验证输入证据有效且比较冲突已决策。按领域边界设计模块目标、范围、需求追踪、领域模型、用例、规则、状态机、API、数据库、事务、并发幂等、事件、缓存、安全、错误码、包结构、测试和迁移策略。每项设计标记 ADOPT_A、ADOPT_B、MERGE、REDESIGN 或 NEW_REQUIREMENT，并引用来源 ID 与理由。

输出 java-target/modules/${module} 的 19 份文档和 decision records。不得复制 PHP 目录结构、逐行翻译 PHP 或在无来源时补业务规则；阻塞项标 REVIEW_REQUIRED。
