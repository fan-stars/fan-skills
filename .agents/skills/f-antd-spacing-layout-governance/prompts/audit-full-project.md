请使用 `$f-antd-spacing-layout-governance` 对当前项目执行完整、只读的 Ant Design 6 布局与间距审计，不要修改代码。

先读取适用的 `AGENTS.md` 并完成项目发现。根据 DOM、背景、定位和交互对页面分类，建立跨页面 Layout Contract；不得因数值不同直接报错。检查 Page/PageContainer、PageSectionList/ContentSectionList、SurfaceSection、ContentStack/StateStack、Module/List/Grid、根 margin、gap 上下文、Token、嵌套容器、safe area、breakpoint、max-width 和 Legacy。标记 Header/Hero、固定头、Overlap、Surface、Drawer、iframe、虚拟列表等例外，并保留 `HEADER-OVERLAY-001` 与 CSS 变量作用域审计。

正则扫描只能产生候选项。按 `templates/spacing-audit-report.md` 输出页面分类证据、布局树、Padding Chain、背景链、gap 所有者、当前/目标归属、共享 primitive 适用性、交互回归点、严重程度、整改阶段和 Top 10。
