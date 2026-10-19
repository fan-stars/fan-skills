请使用 `$f-antd-spacing-layout-governance` 对当前项目做只读的间距响应式审计。

检查 Ant `screen*`、CSS media query、`useBreakpoint`、matchMedia、Tailwind/预处理器、手写 768/992/1200、多个 breakpoint source、PC/H5 过度拆分、媒体查询错误使用 `var(--breakpoint-md)`，以及断点切换后的 Page padding/Module gap 一致性。

输出当前 Breakpoint Sources、source-of-truth 结论、drift 风险、推荐方案、文件/行号和修复优先级。不要修改代码。
