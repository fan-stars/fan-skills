# 分析指定模块

请分析 Project `${project}` 的 `${module}` 模块，范围为 `${requested_scope}`。

分析前按顺序读取 workspace-config、project manifest、source index、symbol index、module index、business index、当前模块文档、上下游摘要、open questions、stale report。定义职责、包含/排除范围、别名、依赖和边界可信度；按路由、表、调用、事件、任务、配置、错误码和状态常量给候选文件打分并解释纳入理由。

递归追踪 Route → Middleware → Controller → Validator → Service → Domain → Repository/Model/SQL → Cache/Event/Job/External → Response。分析 API、数据库、规则、状态、事务、并发幂等、缓存消息任务、权限、跨模块依赖与风险。每个重要结论附 project、相对路径、SHA-256、符号、起止行、证据类型、可信度和 run ID。

更新三层索引和模块多归属标签，生成标准模块文档，执行质量门禁。输出必须列出文档、索引、运行状态、未决问题和失败恢复点。证据不足时标 FACT/INFERENCE/UNRESOLVED/CONFLICT/RISK/DEAD_CODE_CANDIDATE，并将状态保持 PARTIAL 或 REVIEW_REQUIRED。不得读取 Project 另一方作为当前事实，也不得生成 Java 代码。
