请使用 `$f-antd-spacing-layout-governance` 对 `{{SCOPE}}` 执行间距整改。

先读取适用 `AGENTS.md`、Spacing Profile、项目 Layout Contract 和最近 Audit。若 Contract 不存在，先建立并写入项目批准的 profile/decisions。选择两个结构相近页面作为基准，普通同背景页面优先，Surface 页面其次，Overlap、固定头、Drawer、iframe、虚拟列表等例外最后；每次只迁移一个页面或明确层级。

实施前先展示页面分类证据、拟议 DOM 变化、primitive 组合、已安装 Ant Token 的 PC/H5 映射、响应式策略、交互风险和回归计划，等待用户确认。确认后按最小变更执行，不修改业务逻辑，不创建第二套 spacing scale，不用万能 PageLayout，也不为满足规则凭空增加 wrapper。保留既有 Header/Hero、CSS 变量作用域和 safe-area 规则。

完成后运行适用验证和回归审计，输出修改文件、所有权变化、风险、验证结果和剩余 review-required 问题。
