# 变更记录

## 1.1.0

- 将质量门禁候选结果与 `ANALYZED` 最终提交彻底分离，新增同运行 ID 的 `--finalize` 流程并保留历史门禁尝试。
- 新增 `record_reviewed_absence.py`，以 reviewer、时间戳、当前哈希和符号范围安全记录人工确认的 `NOT_APPLICABLE`。
- 修复模块范围校验被最后一个模块名覆盖的问题，校验业务记录关联的 API 与 absence 元数据，并在继续运行前复核实际源码快照。

## 1.0.0

- 建立双项目隔离的源码、符号和业务索引工作流。
- 增加 PHP/SQL 候选解析、哈希证据校验、STALE 检测和质量门禁脚本。
- 提供模块、比较、Java 目标设计模板与最小 PHP fixture。
