# 证据标准

## 目标
保证每条重要结论都能被第三方复核。

## 输入
当前源码、文件哈希、符号索引、行号范围、运行 ID 和结论分类。

## 执行步骤
先计算 SHA-256，再读取完整逻辑块；记录 project、相对路径、symbol、起止行、类型、`semantic_basis`、可信度和 run ID。名称和目录只用于发现候选，不得据此写 FACT/HIGH。

## 输出
符合 evidence schema 的对象，以及 FACT/INFERENCE/UNRESOLVED/CONFLICT/RISK/DEAD_CODE_CANDIDATE 结论。人工确认“不适用”时使用对应 `*_absence` evidence type，并固定 `semantic_basis=reviewed_negative_evidence`。

## 质量检查
验证文件存在、哈希匹配、行范围有效、符号落在范围内且 A/B 路径未越界。

## 失败处理
字段缺失或文件变化时拒绝证据，标记 `INVALID`/`STALE` 和 `REVIEW_REQUIRED`。仅“未搜索到”仍是 `UNRESOLVED`，不得作为负向证据。
