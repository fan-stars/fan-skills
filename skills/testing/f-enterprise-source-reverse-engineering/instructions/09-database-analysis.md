# 数据库分析

## 目标
还原模块表结构、字段语义和代码读写关系。

## 输入
DDL、migration、Model、Repository、query builder、raw SQL、事务和锁证据。

权威 DDL 若位于被索引源码根之外，必须位于分析工作区内，并通过 `extract_sql_tables.py --root <snapshot.sql-or-directory>` 建立 `EXTERNAL_SQL_SNAPSHOT` 表索引。外部记录的 `file` 是工作区相对 POSIX 路径；不得手工跳过文件存在性、实际 SHA-256 和行号范围校验。

## 执行步骤
记录字段、键、索引、外键、状态、枚举、金额/时间单位、JSON、软删除、审计、租户、分片和快照，反向列出读写方法。

## 输出
表清单、字段字典、读写矩阵和关联分类。

## 质量检查
区分数据库外键、代码关联、命名相似和未知；关键字段都有 DDL 或使用证据。外部 SQL 不需要伪装成 source-index 文件，但必须通过 `validate_indexes.py` 或质量门禁的真实性校验。

## 失败处理
DDL 缺失时使用代码查询作为 `INFERENCE`；冲突字段登记 CONFLICT，不自行合并。
