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

## 支持命令

```bash
python3 scripts/build_source_index.py --project A --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/refresh_source_index.py --project A --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/build_symbol_index.py --project A --workspace /path/reverse-workspace
python3 scripts/extract_php_routes.py --project A --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/extract_sql_tables.py --project A --root /path/project-a/database --workspace /path/reverse-workspace
python3 scripts/build_module_index.py --project A --workspace /path/reverse-workspace
python3 scripts/build_business_index.py --project A --module product --analysis-run-id A-product-20260805-001 --workspace /path/reverse-workspace
python3 scripts/query_indexes.py --project A --workspace /path/reverse-workspace --file app/Services/ProductService.php
python3 scripts/query_indexes.py --project A --workspace /path/reverse-workspace --callers-of 'App\Services\ProductService::create'
python3 scripts/evaluate_quality_gates.py --project A --module product --analysis-run-id A-product-20260805-001 --workspace /path/reverse-workspace
python3 scripts/run_analysis.py --project A --module product --root /path/project-a --workspace /path/reverse-workspace
python3 scripts/run_fixture_example.py
python3 scripts/verify_source_evidence.py --workspace /path/reverse-workspace --evidence evidence.json
python3 scripts/detect_stale_references.py --workspace /path/reverse-workspace
python3 scripts/validate_indexes.py --workspace /path/reverse-workspace
```

所有脚本支持 `--help`；路径使用 UTF-8 和 `pathlib`，输出采用原子替换并以跨平台排他锁保护并发更新。`refresh_source_index.py` 复用 size/mtime 未变的记录，`build_symbol_index.py` 复用哈希未变文件的符号。`validate_indexes.py` 和质量门禁必须重新核对单一项目根、实际文件、当前 SHA-256、符号/路由范围、表关联和运行记录，不得只检查字段非空。PHP 符号与路由解析是轻量候选解析，复杂语法须标记 `PARSER_LIMITATION`，不得声称完整 PHP AST 精度。

## 输出与完成标准

模块文档应落在 `reverse-docs/project-a/modules/<module>/`，至少包括分析清单、模块概览、源码图、数据库、API、业务流程/规则、状态机、事务、并发幂等、缓存、事件任务、权限、跨模块依赖、风险、问题和迁移注意事项。必须运行 `evaluate_quality_gates.py`；其 18 项门禁全部通过且证据与本次 `analysis_run_id` 一致后才可标记 `ANALYZED`，否则为 `PARTIAL` 或 `REVIEW_REQUIRED`。门禁进程失败、报告缺失、报告 run ID 不匹配或退出码与报告冲突时，运行必须标记 `FAILED`。使用 `run_analysis.py` 创建唯一 `analysis_run_id` 并记录阶段命令、退出码、读写文件、耗时、缺口与最终状态。

## 禁止行为

禁止混用 A/B 事实、以目录或名称代替证据、伪造行号/哈希、覆盖已有模块标签、每次无条件全量扫描、把推断写成事实、忽略过期引用、在 PHP 逆向阶段生成 Java 代码，或在无来源时补全业务规则。
