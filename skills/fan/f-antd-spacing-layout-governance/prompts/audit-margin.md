请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 做只读 margin 专项审计。

将每个相关 margin 分类为：A 合法对齐 margin；B 合法内部排版 margin；C 可疑 layout margin；D 应迁移为 parent gap；E Legacy/third-party margin。重点检查 `margin-top`、`margin-bottom`、`margin-block` 是否承担 Section、Module、Card/list item 间距。

不要机械判定所有 margin 违规。输出文件、行号、用途分类、父级证据、是否违规、保留/删除/转 parent gap/Adapter 建议和安全等级。
