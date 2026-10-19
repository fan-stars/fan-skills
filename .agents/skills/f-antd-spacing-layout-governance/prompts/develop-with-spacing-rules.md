请使用 `$f-antd-spacing-layout-governance` 开发 `{{FEATURE}}`。

先读取适用 `AGENTS.md`、项目 Profile/Layout Contract 和现有布局。根据 DOM、背景、定位与交互规划页面类型，明确 Page → SectionList → Section/Surface → ModuleList → Module → Content、Padding/背景链、gap 所有者、PC/H5 Ant Token 映射、full-width Surface、safe-area、Header/Hero、固定头、Overlap 和状态职责。

先展示 DOM、primitive 组合、响应式策略和风险并遵守确认流程。优先组合小型职责 primitive，不创建万能 PageLayout 或无职责 wrapper。完成后运行 diff-scoped contract/spacing audit，并验证 PC/H5 的 computed padding、gap、background、关键几何与交互。
