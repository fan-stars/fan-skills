请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 执行只读 Page/Container/Padding 审计。

检查 PageContainer、PageSectionList、ContentSectionList、SurfaceSection、FixedHeaderContent、ContentContainer、Layout/Main、Modal、Drawer、Tabs、Card 和 Table container。识别 padding 所有权冲突、嵌套页面容器、全宽 Surface 被 inline padding 截断、固定头 offset 重复、首尾空间由子 margin 补齐及 max-width 漂移。

输出 Container Tree、Padding Chain、背景链和直接 sibling gap 所有者；对每个异常明确当前归属、目标归属、共享 primitive 适用性、交互回归点和安全等级。不要修改代码。
