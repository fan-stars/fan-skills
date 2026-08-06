# 失败恢复

## 目标
在扫描、解析、写入或源码变化后安全恢复。

## 输入
上一版索引、运行日志、临时文件、错误信息、当前源码哈希和 stale 报告。

## 执行步骤
保留上一版，清理孤立临时文件，定位失败阶段；对同一 project/module/root 使用原 `analysis_run_id` 执行 `python3 scripts/run_analysis.py ... --resume`，从首个失败阶段继续。运行正常结束为 `PARTIAL` 或 `REVIEW_REQUIRED` 时，补齐文档和人工复核证据后执行同一 ID 的 `python3 scripts/run_analysis.py ... --finalize`，只重跑门禁并保留上次门禁尝试。两个继续入口都会重读实际源码集合、哈希和行数，且继续流程的门禁不使用旧可信快照；源码或 source-index 已变化时拒绝继续，应增量刷新并创建新运行重新验证证据。

## 输出
FAILED/PARTIAL 运行记录、恢复动作、受影响模块、需复核文档和下一步命令。

## 质量检查
确认没有写入业务源码，索引可解析且原子替换完整，旧证据未被静默重写；恢复后阶段列表必须仍是固定顺序且无重复，`resume_count` 与 `resumed_at`、`finalization_count` 与 `finalized_at` 数量一致，历史门禁保存在 `quality_gate_attempts`。

## 失败处理
连续失败时停止扩展范围并请求修复路径、权限或依赖，不用降级结果冒充完成。
