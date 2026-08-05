# 分类 UNKNOWN 文件

对 Project `${project}` 中候选模块 `${module}` 的 UNKNOWN 文件进行分类。

输入 workspace `${workspace_root}`、模块别名 `${aliases}` 和最小分数 `${threshold}`。读取 module/source/symbol/business indexes，结合路由、核心表、调用/被调用、事件、Job、配置键、错误码、状态常量和历史业务条目打分；文件名/注释只能低权重。逐文件列出信号、证据、分数和纳入/排除理由。

只通过 `update_module_ownership.py` 追加 PRIMARY/SECONDARY/SHARED/INFRASTRUCTURE/UNKNOWN 标签，不覆盖已有标签。输出分类清单、仍未知文件和 open questions。置信度不足时保持 UNKNOWN，不允许为清零未知数量而强制归类。索引更新失败时返回非零状态并保留原标签。
