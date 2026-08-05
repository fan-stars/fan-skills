# 检查过期引用

检查 workspace `${workspace_root}` 的 `${project_or_both}` stale references。

读取 source/symbol/business/module indexes 和已有 stale report，运行 `detect_stale_references.py`，按项目、模块、接口、规则和文档分组。对每个变化文件说明旧哈希、当前哈希或删除状态、模块归属和受影响证据；A/B 结果分开保存。

输出过期数量、受影响对象、需重新分析文档和建议优先级。不要修改源码、不要静默删除旧证据、不要猜测新行号。命令非零退出或索引缺失时将运行标 FAILED/PARTIAL，并在失败清单中记录缺失索引、命令和恢复步骤。
