请使用 `$f-antd-spacing-layout-governance` 对当前项目做只读 Ant Design spacing Token 审计。

核对实际安装版本和 `ConfigProvider/cssVar` 配置。检查 spacing hardcode、有效/无效 margin/padding token、CSS 变量名、重复自定义 spacing scale、gap 合理复用 margin token 尺寸、Component Token 边界、JS/CSS 双份数值和 `calc()` 内硬编码 spacing。

输出 Token inventory、Custom token inventory、重复映射、无效使用、hardcode、源码位置和渐进迁移计划。不要把尺寸、max-width、border、breakpoint、图形或合法 `env()` 当 spacing。
