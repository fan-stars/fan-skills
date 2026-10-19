请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 做只读 gap 专项审计。

检查所有 `gap`/`row-gap`/`column-gap`：是否运行于 flex/inline-flex/grid、是否使用当前 Ant spacing token 尺寸、是否与 direct child layout margin 重复、是否被误作首尾 padding、是否错误期待管理深层元素、同类列表是否不一致、是否硬编码、Space/Flex/Grid 选型是否合理、公共布局是否需要解释 margin token 仅复用尺寸。

逐项输出源码位置、上下文、规则、影响、建议和修复安全等级。不要修改代码，扫描命中不能直接算问题。
