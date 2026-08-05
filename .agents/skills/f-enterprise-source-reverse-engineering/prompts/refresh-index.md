# 增量刷新索引

请增量刷新 `${project}` 的索引，workspace 为 `${workspace_root}`，仓库为 `${repository_root}`。

先读取 manifest、source/symbol/module/business index、上一运行和 stale 报告。比较当前文件与旧记录，保留已有模块标签；记录新增、修改、删除；哈希变化或删除的已有证据标记 `STALE`，受影响文档标 `REVIEW_REQUIRED`。仅当根目录变化、版本无效或大规模变化时才全量重建。

禁止修改仓库源码，所有输出使用临时文件加原子替换。输出变更明细、受影响模块/API/规则/文档、索引版本和复核命令。写入或校验失败时保留旧索引并返回非零状态。
