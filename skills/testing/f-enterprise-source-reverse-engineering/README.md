# 企业级源码逆向工程

这是一套面向大型 PHP 遗留系统的证据化逆向分析技能。它与普通代码总结的区别是：A、B 两个项目事实完全隔离；源码、符号、业务语义分三层持久化；结论必须绑定当前文件 SHA-256、符号和真实行号；文件变化会自动产生 `STALE` 报告。

## 快速使用

```text
初始化双 PHP 项目逆向分析工作区。Project A 路径为……，Project B 路径为……，数据库结构目录为……。
为 Project A 建立完整源码、符号和基础数据库索引。
分析 Project A 的商品模块；先读取现有索引，所有结论附准确源码路径和行号。
比较 Project A 和 Project B 的订单模块，输出能力、规则、状态机、事务、幂等和风险差异。
结合两套订单模块、比较报告和 REQ-ORDER 需求，生成新的 Java 订单模块设计文档。
```

分析顺序是独立逆向 A/B、比较、Java 目标设计、实现。Java 设计必须注明 `ADOPT_A`、`ADOPT_B`、`MERGE`、`REDESIGN` 或 `NEW_REQUIREMENT`，不能在逆向阶段生成 Java 代码。

## 工具与测试

脚本本身只依赖 Python 3.9+ 标准库。Schema 测试和平台 Front Matter 校验需要测试依赖：

```bash
python3 -m venv .venv
# Linux/macOS
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -v
# Windows PowerShell
.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

从技能目录运行 `scripts/*.py --help`。先用 `build_source_index.py` 建索引并用 `update_module_ownership.py` 写入有证据的模块归属，再运行 `run_analysis.py`；它会调用真实存在的 source/symbol/route/table/module/business 索引脚本和 18 项质量门禁。门禁会验证实际文件、当前哈希、符号或路由行号、表关联及本次运行记录；门禁进程失败或报告 run ID 不匹配时，分析运行记为 `FAILED`。`query_indexes.py` 可查询文件归属、方法反向调用者及业务规则关联的接口与表。`detect_stale_references.py` 会在项目边界内把变化传播到 API、业务和模块索引。运行 `python3 scripts/run_fixture_example.py` 可实际执行内置 fixture、查询调用者和业务规则并显示门禁结果。

## 变化与安装排查

刷新后若文件哈希改变，旧证据只能标为 `STALE`，对应文档标记 `REVIEW_REQUIRED`。SKILL.md 第一字节必须是 `-`，第一行必须是 `---`；`name` 不能为空；结束 `---` 必须存在；Front Matter 前不能有 BOM、空行或其他字符；只使用平台支持字段。运行 `python3 <skill-creator-dir>/scripts/quick_validate.py <skill-dir>` 检查基本格式，并以当前平台实际安装路径替换尖括号参数；该平台脚本需要 `PyYAML`，已列入 `tests/requirements.txt`。
