# 业务知识索引

## 目标
把源码证据提升为可查询的业务语义，而不复制目录名。

## 输入
模块文档、符号/表/API 索引、证据对象、需求和运行 ID。

## 执行步骤
建立 module、use_case、api、business_rule、state_transition、transaction、idempotency_rule、permission_rule、event、job、risk、open_question、decision、requirement 条目。经完整范围人工复核后，可用 `business_rule_absence`、`state_transition_absence`、`concurrency_idempotency_absence`、`cross_module_dependency_absence` 记录不适用，并填写 rationale 与 reviewed negative evidence。

## 输出
带分类、置信度、证据数组、相关对象和 run ID 的 business-index JSONL。

## 质量检查
每条规则至少一个实现证据；推断、冲突、风险和未决问题不能伪装成 FACT。absence 记录至少一个当前、可定位的复核范围证据；自动构建器不得生成 absence。

## 失败处理
语义无法确认时创建 `UNRESOLVED` 条目并保留候选证据，不删除已有记录。
