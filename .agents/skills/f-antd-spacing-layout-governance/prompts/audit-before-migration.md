请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 做整改前只读风险审计，不要修改源码。

先对页面分类并读取项目 Layout Contract。识别复杂 DOM、Surface/Overlap、固定或透明 Header、Drawer、iframe、Virtual List、Drag/Drop、animation、third-party、继承/全局样式、margin collapsing、overflow/scroll container 和 selector coupling。还原布局树、Padding/背景链、gap 所有者与视觉意图。

将候选修改分成 SAFE、REVIEW REQUIRED、DO NOT AUTO FIX，并提供当前/目标归属、primitive 适用性、拟议 DOM 变化、Token/响应式策略、交互风险和下一步边界。
