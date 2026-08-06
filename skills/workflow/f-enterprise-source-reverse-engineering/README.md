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

Linux/macOS（在技能目录执行，但把虚拟环境放到技能目录外，避免污染内容哈希）：

```bash
python3 -m venv /tmp/f-esre-venv
/tmp/f-esre-venv/bin/python -m pip install -r tests/requirements.txt
/tmp/f-esre-venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell：

```powershell
$venv = Join-Path $env:TEMP "f-esre-venv"
py -m venv $venv
& "$venv\Scripts\python.exe" -m pip install -r tests\requirements.txt
& "$venv\Scripts\python.exe" -m unittest discover -s tests -v
```

从技能目录运行 `python3 scripts/<script>.py --help`。先用 `build_source_index.py` 建索引并用 `update_module_ownership.py` 写入有证据的模块归属，再运行 `run_analysis.py`；它会调用真实存在的 source/stale/symbol/route/table/module/business 索引脚本和 18 项质量门禁。失败后用原命令加 `--analysis-run-id <原ID> --resume`，只从首个失败阶段继续。正常结束为 `PARTIAL`/`REVIEW_REQUIRED` 时，用 `record_reviewed_absence.py` 安全写入人工确认的不适用维度，补齐文档后以同一运行 ID 加 `--finalize`，只重跑门禁并保留历史门禁尝试。`--resume`/`--finalize` 都会重新核对实际源码集合、哈希和行数；源码已变化时必须创建新运行。同一文件可以追加多个模块；同一文件/模块需要改 role 时必须显式加 `update_module_ownership.py --replace-role`。

SQL DDL 可以来自源码根内的 migration/database 目录，也可以来自分析工作区内的权威 `.sql` 快照。外部快照应把具体文件或专用目录传给 `extract_sql_tables.py --root`/`run_analysis.py --sql-root`；生成记录会标记 `source_scope=EXTERNAL_SQL_SNAPSHOT` 并使用工作区相对路径。此类记录不要求出现在 PHP 项目的 `source-index`，但门禁仍会读取实际文件并校验 SHA-256 与行号范围；快照位于工作区外、路径逃逸、文件缺失、哈希变化或行号越界都会失败。旧工作区中带精确“外部数据库快照”说明的记录可兼容验证，建议下次索引时由官方脚本补齐显式范围字段。

A/B 在同一工作区绑定到两个不同且不可静默切换的源码根。门禁会验证实际文件、当前哈希、符号/路由范围、调用可达性、表关联、类型化业务字段、必需模块文档及本次运行记录；独立执行门禁只产生候选结果，只有 `run_analysis.py` 完成最终运行记录校验后才提交模块、API 和业务记录为 `ANALYZED`。名称后缀只产生 `MEDIUM` 候选，不能产生事实证据；自动扫描未发现某维度时保持 `UNRESOLVED`，不能自动标 `NOT_APPLICABLE`。人工 absence 证据必须记录 reviewer、reviewed_at、当前哈希、符号范围和运行 ID。`query_indexes.py` 可查询文件归属、方法反向调用者及业务规则关联的接口与表。`refresh_source_index.py` 会自动把变化传播到 API、业务和模块索引。运行 `python3 scripts/run_fixture_example.py` 可实际执行内置 fixture；fixture 有意缺少模块文档、状态迁移、幂等和跨模块证据，预期门禁结果是 `PARTIAL` 14/18，不是完成声明。

## 变化与安装排查

刷新后若文件哈希改变，旧证据只能标为 `STALE`，对应文档标记 `REVIEW_REQUIRED`。默认增量判断复用 size/mtime；怀疑工具保留时间戳时使用 `refresh_source_index.py --verify-all` 强制重新哈希。SKILL.md 第一字节必须是 `-`，第一行必须是 `---`；`name` 不能为空；结束 `---` 必须存在；Front Matter 前不能有 BOM、空行或其他字符；只使用平台支持字段。运行 `python3 <skill-creator-dir>/scripts/quick_validate.py <skill-dir>` 检查基本格式，并以当前平台实际安装路径替换尖括号参数；该平台脚本需要 `PyYAML`，已列入 `tests/requirements.txt`。
