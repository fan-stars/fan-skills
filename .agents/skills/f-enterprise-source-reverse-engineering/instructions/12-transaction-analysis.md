# 事务分析

## 目标
确定跨表更新的原子边界和异常行为。

## 输入
transaction begin/commit/rollback、ORM wrapper、异常处理、锁和外部调用实现。

## 执行步骤
从接口和任务入口追踪事务开启、嵌套、提交/回滚、锁、隔离级别及外部调用位置。

## 输出
事务边界图、原子性结论、异常传播、锁证据和未发现事务说明。

## 质量检查
每个核心流程明确事务入口或“已检查但未发现”；事务内副作用必须登记。“已检查但未发现”先保持 `UNRESOLVED`；只有复核完整可达调用图并通过 `record_reviewed_absence.py --dimension transaction` 写入 `transaction_absence`、rationale、reviewer、reviewed_at 和 `reviewed_negative_evidence` 后才能标 `NOT_APPLICABLE`。

## 失败处理
框架封装无法解析时标 PARSER_LIMITATION/INFERENCE，保持 REVIEW_REQUIRED。
