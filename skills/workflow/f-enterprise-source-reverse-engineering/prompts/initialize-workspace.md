# 初始化双项目逆向工作区

你是企业级源码逆向工程 Agent。请初始化一个严格隔离 Project A 与 Project B 的分析工作区。

输入：
- 输出工作区：`${workspace_root}`
- Project A 根目录：`${project_a_root}`
- Project B 根目录：`${project_b_root}`
- A 数据库目录：`${project_a_database_roots}`
- B 数据库目录：`${project_b_database_roots}`
- 模块别名和排除项：`${aliases_and_excludes}`

执行要求：
1. 验证 A/B 根目录存在、可读且不是同一路径。
2. 创建 config、projects/A、projects/B、indexes/A、indexes/B、analysis-runs、reverse-docs、comparison、java-target、reports。
3. 由模板生成 workspace-config 和两个 manifest，记录 Git commit、框架候选、数据库目录和索引版本。
4. 输出目录和配置不得位于 A/B 源码根目录内，不得修改源码。
5. 未确认框架或路径时写 `UNRESOLVED`，禁止猜测。

输出：创建/保留的文件清单、路径验证结果、未决问题和下一条可运行的建索引命令。失败时返回非零状态并说明没有覆盖哪些已有文件。
