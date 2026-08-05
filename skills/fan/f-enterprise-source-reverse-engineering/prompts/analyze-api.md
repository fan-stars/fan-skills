# 分析单个 API

分析 Project `${project}` 中 `${method} ${path}`，模块 `${module}`，workspace `${workspace_root}`。

必须从真实路由定义开始，追踪 Middleware、Controller、Request Validator、核心 Service、Domain、Repository/Model/SQL、事务、缓存、事件/Queue/Job、外部服务和 Response Mapper。记录 API ID、路由名、path/query/body/header、认证、权限、校验、响应、错误码、读写表、事务边界、缓存、异步、幂等、并发、副作用和完整调用链。

每个链路节点必须有当前 SHA-256、符号、完整逻辑行范围和 semantic_basis。名称后缀只产生 MEDIUM candidate。每个覆盖维度明确 PRESENT/UNRESOLVED；只有人工复核完整调用范围并提供 reviewed_negative_evidence 才能写 NOT_APPLICABLE。输出 api-detail、API 索引更新、业务规则/状态变化和 open questions；门禁最终提交前接口保持 `PARTIAL`。
