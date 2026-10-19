请使用 `$f-antd-spacing-layout-governance` 把当前 Git diff 当作 PR，仅只读审计本次新增/修改代码的 Layout/Spacing。

检查新 hardcode、根 margin、gap + margin、gap 无 flex/grid、容器嵌套、safe area、错误 Token、breakpoint 和 max-width。若 diff 改变页面分类契约、Surface 背景、Overlap、固定头 offset、StateStack、Header/Hero 或变量作用域，检查对应 `LAYOUT-*`/`HEADER-OVERLAY-001` 回归。报告无真实职责的 wrapper 和带大量互斥布尔参数的万能 PageLayout。不要混入历史问题。

按 Blocking / Non-blocking / Suggestions 输出；每项给出文件、diff 行号、当前/目标归属、受影响交互、原因、建议和安全等级。
