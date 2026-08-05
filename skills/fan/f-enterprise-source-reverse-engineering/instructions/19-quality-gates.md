# 质量门禁

## 目标
阻止证据不足的模块被标记为 ANALYZED。

## 输入
索引、模块文档、证据校验结果、stale 报告、风险和 open questions。

## 执行步骤
运行 `scripts/evaluate_quality_gates.py`，检查源码索引、符号索引、业务索引、模块归属、路由、Controller、验证、Service、持久化、表、业务规则、状态迁移、事务、并发/幂等、副作用、跨模块依赖、证据时效和运行记录共 18 项。

## 输出
门禁报告和最终状态：全部满足才是 ANALYZED，否则 PARTIAL 或 REVIEW_REQUIRED。

## 质量检查
报告逐项写入 `reports/<project>/<module>-quality-gates.json`；未全部通过时脚本退出 2。全部通过只产生候选 `ANALYZED`，完整运行记录校验落盘后才原子提交模块、API 与业务记录。PRESENT 必须有正向类型证据；NOT_APPLICABLE 必须有 reviewed negative evidence；UNRESOLVED 不通过对应门禁。

## 失败处理
任一项缺失时保留文档，补证后重跑，不降低门槛或删除失败记录。直接运行门禁默认重哈希实际源码；`--trust-source-index` 必须同时提供匹配的单项目 `--source-snapshot-id`，只用于同一自动管线刚生成的快照。
