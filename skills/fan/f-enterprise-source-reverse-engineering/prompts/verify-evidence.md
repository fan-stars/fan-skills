# 重新验证源码证据

验证 workspace `${workspace_root}` 中 Project `${project}`、模块 `${module_or_all}` 的证据集合 `${evidence_scope}`。

逐条检查必填字段、项目边界、文件存在、当前 SHA-256、行号范围、符号是否仍在范围内、是否引用排除目录。运行仓库实际存在的 `verify_source_evidence.py`；记录命令、退出码和错误，不得伪造结果。

输出有效、STALE、INVALID 证据清单，受影响模块/API/规则/文档和重新分析建议。哈希变化时不得自动平移旧行号；只有重读实现并生成新证据后才能关闭 REVIEW_REQUIRED。脚本失败时报告失败，不声称验证通过。
