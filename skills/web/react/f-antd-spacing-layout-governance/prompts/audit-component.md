请使用 `$f-antd-spacing-layout-governance` 只读审计组件 `{{COMPONENT}}` 是否是可复用 Module。

检查根节点是否携带页面布局 margin、是否自行决定兄弟距离、内部是否由父级 gap 管理、gap + child margin、gap 是否处于 flex/grid、padding/token、重复 spacing 变量、Ant 原生组件内部覆盖、PC/H5 差异、对特殊父级的隐式依赖。

输出 Module 合规结论、语义层级、问题（文件/行号/规则/严重度）、修复建议、安全等级和推荐 DOM/Layout 结构。不要修改代码。
