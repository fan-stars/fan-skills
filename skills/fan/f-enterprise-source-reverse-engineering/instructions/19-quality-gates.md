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
报告逐项写入 `reports/<project>/<module>-quality-gates.json`；未全部通过时脚本退出 2，并把模块保持为 `PARTIAL` 或 `REVIEW_REQUIRED`。

## 失败处理
任一项缺失时保留文档，补证后重跑，不降低门槛或删除失败记录。
