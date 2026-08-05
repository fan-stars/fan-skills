# 建立全局索引

请为 `${project=A|B}` 建立完整的源码、符号、路由候选和数据库表索引。

输入：workspace `${workspace_root}`；仓库 `${repository_root}`；数据库目录 `${database_roots}`；排除规则 `${excludes}`。

严格执行：先读取 workspace-config 和该项目 manifest；生成唯一 analysis_run_id；运行 build_source_index、build_symbol_index、extract_php_routes、extract_sql_tables；只写 `${workspace_root}/indexes/${project}` 和运行记录；不得读取另一项目业务结果作为事实。轻量 PHP/路由解析只输出候选并标记解析限制。

输出必须包含：文件/符号/路由/表数量、新增/修改/删除文件、排除与失败文件、索引版本、实际运行命令和退出码。最后运行 validate_indexes；任何校验失败都将状态设为 `FAILED` 或 `PARTIAL`，不得报告完成。
