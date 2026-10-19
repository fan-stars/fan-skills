请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 做只读 H5 间距与 Safe Area 审计。

检查 MobilePageContainer、BottomNav、StickyActionBar、`safe-area-inset-bottom`、fixed/sticky、内容遮挡、safe area 重复/缺失、BottomNav height 所有权、page bottom padding、H5 Module gap、全宽 Banner 和业务组件页面 margin。

输出 Safe Area Responsibility Map、Bottom Offset Calculation、重复/缺失问题、文件/行号和统一实现建议。必须先判断 BottomNav height 是否已包含 safe area。
