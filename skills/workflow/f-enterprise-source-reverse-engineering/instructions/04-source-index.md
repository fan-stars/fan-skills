# 源码索引

## 目标
保存每个有效源码和配置文件的可比较快照。

## 输入
项目根目录、排除规则、上次 source-index 和当前时间。

## 执行步骤
流式遍历，计算大小/行数/mtime/SHA-256，保留模块标签，检测新增、修改、删除；已有证据的修改/删除标记 STALE。

## 输出
项目独立 source-index JSONL、index-manifest 和变更报告。

## 质量检查
检查 project、relative_path、absolute_path、sha256、line_count、analysis_status、modules，并确认不写源码根目录。

## 失败处理
读文件失败记录原因并保留旧索引；原子替换失败时删除临时文件并返回非零码。
