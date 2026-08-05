# API 分析

## 目标
为每个接口建立从路由到副作用的完整证据链。

## 输入
路由、Controller/Validator/Service/Repository/Model、缓存、事件、任务和配置。

## 执行步骤
记录 method/path/参数/认证/权限/错误，追踪持久化、事务、缓存、异步和外部服务，再记录返回、幂等和并发。

## 输出
接口文档、调用链、读写表和 open questions。

## 质量检查
路由、入口、验证、核心 Service、持久化、事务、异步/外部调用和响应映射均有哈希行号；推断标 `INFERENCE`。

## 失败处理
链路断点保持 `PARTIAL`，记录缺失证据和下一步搜索范围。
