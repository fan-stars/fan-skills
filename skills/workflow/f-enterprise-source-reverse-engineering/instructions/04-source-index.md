# 源码索引

## 目标
保存每个有效源码和配置文件的可比较快照。

## 输入
项目根目录、排除规则、上次 source-index 和当前时间。

## 执行步骤
流式遍历，计算大小/行数/mtime/SHA-256，保留模块标签，检测新增、修改、删除；刷新命令自动传播已有证据为 STALE。默认用 size/mtime 增量复用，时间戳可能被保留时使用 `--verify-all`。

## 输出
项目独立 source-index JSONL、index-manifest 和变更报告。

## 质量检查
检查 project、relative_path、absolute_path、sha256、line_count、analysis_status、modules，并确认不写源码根目录。manifest 同时绑定 `source_index_sha256` 与 `snapshot_id`；可信模式必须二者匹配。

## 失败处理
读文件失败记录原因并保留旧索引；原子替换失败时删除临时文件并返回非零码。可信模式仅供刚完成 source refresh 的单项目管线使用，独立审计保持默认全量复核或显式 `--verify-all`。
