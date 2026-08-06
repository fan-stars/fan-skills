---
name: f-enterprise-source-reverse-engineering
description: >
  Evidence-first reverse engineering of two large PHP systems, module by module,
  with isolated persistent indexes, exact file hashes and line ranges, API,
  database, state, transaction, concurrency and risk analysis. Use when
  initializing or refreshing a dual-project workspace, analyzing a PHP module,
  validating source evidence, comparing Project A and B, or designing a traceable
  Java target system from approved findings.
---

# 企业级源码逆向工程

将两套遗留 PHP 系统当作两个独立事实源，按模块建立可增量刷新的源码、符号和业务索引，并用可复核的文件哈希、符号和行号输出设计文档。本技能只负责逆向、比较和 Java 目标设计，不在阶段一把 PHP 逐行翻译成 Java。

## 何时启用

用户要求初始化双项目逆向工作区、建立或刷新索引、分析商品/订单/支付等模块、验证证据或过期引用、比较两套同类模块，或依据比较结论与新需求设计 Java 模块时启用。

## 入口与资源

- 先读 `instructions/00-overview.md` 与 `instructions/02-analysis-lifecycle.md`，再按任务读取对应专题指引。
- 需要模板时读取 `templates/` 中对应文件；需要字段约束时读取 `schemas/`。
- 运行索引与证据检查使用 `scripts/`，全部脚本只写分析工作区，不修改被分析源码。
- 示例和最小 fixture 位于 `examples/`、`tests/fixtures/`。

## 强制上下文加载顺序

每次模块分析前，按顺序读取：`workspace-config`、项目 manifest、源码索引、符号索引、模块索引、业务索引、当前模块已有文档、上下游模块摘要、open questions、stale reference report。缺失时记录为 `UNRESOLVED`，不得用猜测补齐。

## 四阶段流程

1. **分别逆向 A/B**：初始化配置，分别建立全量索引；按候选评分追踪 Route → Controller → Validator → Service → Repository/Model/SQL → Cache/Event/Job/外部调用 → Response。
2. **比较**：只有两边模块达到至少 `PARTIAL`、证据未过期且边界可对齐时，才生成能力、数据、API、规则、状态、事务、并发、幂等和风险比较。
3. **Java 目标设计**：读取双方文档、比较报告、决策登记、新需求与相关模块摘要；每项设计标记 `ADOPT_A`、`ADOPT_B`、`MERGE`、`REDESIGN` 或 `NEW_REQUIREMENT`。
4. **实现**：把已批准的 Java 设计交给实现技能；本技能不直接生成 Java 代码。

## 证据与事实隔离

重要结论必须是 `FACT`、`INFERENCE`、`UNRESOLVED`、`CONFLICT`、`RISK` 或 `DEAD_CODE_CANDIDATE`，并附项目、相对路径、SHA-256、符号、起止行、证据类型、可信度和 `analysis_run_id`。名称只能发现候选，不能作为事实。A/B 的所有索引、文档、运行记录、风险和问题目录必须独立；比较阶段才允许跨项目引用。

一个文件可有多个模块归属，使用 `PRIMARY`、`SECONDARY`、`SHARED`、`INFRASTRUCTURE`、`UNKNOWN`，追加标签而非覆盖。文件哈希变化后旧证据标为 `STALE`，文档标为 `REVIEW_REQUIRED`，重新验证行号。

自动索引器只把结构关系写为事实：路由声明、路由处理器、带 `rules()` 的请求类型、可达的编排调用、已关联表的持久化调用、事务和副作用调用。`*Service`、`*Repository`、`*Model`、`*Request` 等名称信号只能写入 `candidates`，置信度最多 `MEDIUM`。某维度无实现时保持 `UNRESOLVED`；只有人工复核完整可达范围并通过 `record_reviewed_absence.py` 写入带 reviewer、reviewed_at、当前哈希和 `semantic_basis: reviewed_negative_evidence` 的证据后，才能标为 `NOT_APPLICABLE`。质量门禁只生成候选状态，禁止独立门禁进程直接提交 `ANALYZED`；补证后必须使用同一运行 ID 的 `--finalize`，由运行记录校验完成两阶段提交。

## 支持命令

```bash
python3 scripts/build_source_index.py --project A --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/refresh_source_index.py --project A --root /path/project-a --workspace /path/reverse-workspace --verify-all
python3 scripts/build_symbol_index.py --project A --workspace /path/reverse-workspace
python3 scripts/extract_php_routes.py --project A --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/extract_sql_tables.py --project A --root /path/project-a/database --workspace /path/reverse-workspace
python3 scripts/build_module_index.py --project A --workspace /path/reverse-workspace
python3 scripts/build_business_index.py --project A --module product --analysis-run-id A-product-20260805-001 --workspace /path/reverse-workspace
python3 scripts/query_indexes.py --project A --workspace /path/reverse-workspace --file app/Services/ProductService.php
python3 scripts/query_indexes.py --project A --workspace /path/reverse-workspace --callers-of 'App\Services\ProductService::create'
python3 scripts/evaluate_quality_gates.py --project A --module product --analysis-run-id A-product-20260805-001 --workspace /path/reverse-workspace
python3 scripts/run_analysis.py --project A --module product --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/run_analysis.py --project A --module product --root /path/project-a --workspace /path/reverse-workspace --analysis-run-id A-product-20260805-001 --resume
python3 scripts/record_reviewed_absence.py --project A --module product --api-id A-PRODUCT-API-001 --dimension transaction --rationale '完整复核入口到可达调用图，未发现事务边界' --reviewer TICKET-123 --analysis-run-id A-product-20260805-001 --workspace /path/reverse-workspace
python3 scripts/run_analysis.py --project A --module product --root /path/project-a --workspace /path/reverse-workspace --analysis-run-id A-product-20260805-001 --finalize
python3 scripts/run_fixture_example.py
python3 scripts/verify_source_evidence.py --workspace /path/reverse-workspace --evidence evidence.json
python3 scripts/detect_stale_references.py --workspace /path/reverse-workspace
python3 scripts/validate_indexes.py --workspace /path/reverse-workspace
```

所有脚本支持 `--help`；路径使用 UTF-8 和 `pathlib`，输出采用原子替换并以可恢复的跨平台排他锁保护并发更新。A/B 在工作区内绑定不同源码根，下游索引器在读取事实前验证 project/root/path。默认增量复用 size/mtime 未变的记录；`--verify-all` 强制重算哈希，符号、路由和 SQL 表索引按哈希复用。独立运行 `validate_indexes.py`、质量门禁或 stale 检测时默认重读实际源码；自动管线只在刚完成源码刷新后，以 manifest 中匹配的 `snapshot_id` 和 source-index 哈希启用可信快照，禁止单独使用无 token 的 `--trust-source-index`。PHP 符号与路由解析是轻量候选解析，复杂语法须标记 `PARSER_LIMITATION`，不得声称完整 PHP AST 精度。

## 输出与完成标准

模块文档应落在 `reverse-docs/project-a/modules/<module>/`，至少包括分析清单、模块概览、源码图、数据库、API、业务流程/规则、状态机、事务、并发幂等、缓存、事件任务、权限、跨模块依赖、风险、问题和迁移注意事项。必须运行 `evaluate_quality_gates.py`；其 18 项门禁全部通过、类型化业务字段齐全、证据与本次 `analysis_run_id` 一致且最终运行记录校验通过后，才以两阶段提交把模块、API 和业务记录标记为 `ANALYZED`，否则保持 `PARTIAL` 或 `REVIEW_REQUIRED`。门禁进程失败、报告缺失、报告 run ID 不匹配、退出码与报告冲突或最终记录不完整时，运行必须标记 `FAILED`。使用 `run_analysis.py` 创建唯一 `analysis_run_id`；失败后用同一 ID 加 `--resume` 从首个失败阶段继续。运行记录的 `record_scope` 为 `AUTOMATED_PIPELINE`，只声明自动管线实际扫描、读取、复用和写入的文件，不冒充人工或模型的全部上下文访问日志。

## 禁止行为

禁止混用 A/B 事实、以目录或名称代替证据、伪造行号/哈希、覆盖已有模块标签、每次无条件全量扫描、把推断写成事实、忽略过期引用、在 PHP 逆向阶段生成 Java 代码，或在无来源时补全业务规则。
