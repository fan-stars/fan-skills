# 分析模块数据库

分析 Project `${project}` 的 `${module}` 数据库设计，数据库目录 `${database_roots}`。

联合读取 CREATE TABLE、migration、Model、Repository、query builder、raw SQL、join、insert/update/delete、事务、锁、唯一键和索引。区分核心表、辅助表、关联表和跨模块表；逐表记录字段、主键、唯一键、普通索引、数据库外键、代码关联、状态/枚举、金额/时间单位、时区、JSON/序列化、软删除、审计、租户、分片、快照和冗余字段。

反向列出读/写/删除方法、相关 API、事务和状态迁移，每项附源码证据。数据库明确外键、代码推断关联、名称相似和未知必须分开。输出数据库文档、table/business index 更新、冲突和 open questions；不得只根据表字段名下结论。
