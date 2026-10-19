请使用 `$f-antd-spacing-layout-governance` 对刚完成整改的 `{{SCOPE}}` 做回归审计。

确认 Layout Contract、原问题、所有权、gap + margin、double padding、背景边界、safe area、breakpoint、新 hardcode 和无关业务改动。PC/H5 各验证一个目标：computed page/section padding、direct-sibling gap、background、Header/Hero 或固定头几何、关键锚点、StateStack、Overlap、Drawer 与滚动交互。透明覆盖模式继续要求 `hero.top ≈ 0`；固定实心头要求恰好一次 offset；Surface 背景不得被截断。浏览器不可用时明确报告视觉验证受阻。

输出 Resolved、Remaining、Regressions、Validation Results；所有剩余/回归问题必须给文件和行号。
