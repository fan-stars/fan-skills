请使用 `$f-antd-spacing-layout-governance` 对页面 `{{PAGE}}` 做只读深度间距审计，只覆盖该页面及其直接依赖的布局和业务组件。

先根据 DOM、背景、定位和交互对页面分类；证据不足时保持未分类。还原 Page → SectionList → Section/Surface → ModuleList → Module → Content，输出 Padding Chain、背景链和每组直接 sibling 的 gap 所有者。标记 Header/Hero、固定头、safe area、Overlap、Surface、Drawer、iframe 等例外，并检查根 margin、嵌套容器、响应式和 Token 映射。若存在首屏 Hero，继续执行既有 Header 状态、几何和 CSS 变量作用域检查。

输出分类证据、布局树、Padding/背景链、当前与目标归属、共享 primitive 适用性、PC/H5 Token 映射、交互回归点及 safe/review-required/unsafe 分类。不同数值只有在语义责任相同时才可判为不一致。不要修改代码。
