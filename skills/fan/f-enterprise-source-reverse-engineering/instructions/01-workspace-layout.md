# 工作区布局

## 目标
让配置、索引、运行记录和文档具备稳定职责边界。

## 输入
两个仓库绝对路径、数据库目录、模块别名、排除目录和输出根目录。

## 执行步骤
创建 `config`、`projects/A|B`、`indexes/A|B`、`analysis-runs/A|B`、`reverse-docs`、`comparison`、`java-target`、`reports`，分别写 A/B manifest。

## 输出
workspace-config、Project A/B manifest 和目录清单。

## 质量检查
验证根目录不同、manifest project 值正确、输出路径不在业务源码根目录内。

## 失败处理
路径不存在、不可读或越界时拒绝初始化；保留已有工作区，不覆盖索引。
