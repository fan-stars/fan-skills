# API 分析

## 目标
为每个接口建立从路由到副作用的完整证据链。

## 输入
路由、Controller/Validator/Service/Repository/Model、缓存、事件、任务和配置。

## 执行步骤
记录 method/path/参数/认证/权限/错误，追踪持久化、事务、缓存、异步和外部服务，再记录返回、幂等和并发。validation/service/persistence/transaction/side_effect/tables 每维填写 `PRESENT`、`UNRESOLVED` 或经人工复核的 `NOT_APPLICABLE`；自动索引只产出前两种。

## 输出
接口文档、调用链、读写表和 open questions。

## 质量检查
路由和入口必须有结构证据；验证需控制器参数关联带 `rules()` 的类型；Service 需可达且确有持久化、事务或副作用编排；持久化需关联已知表。类名后缀只进入 candidates。API 在模块全部门禁和最终运行记录提交前保持 `PARTIAL`。

## 失败处理
链路断点保持 `PARTIAL`，记录缺失证据和下一步搜索范围。
