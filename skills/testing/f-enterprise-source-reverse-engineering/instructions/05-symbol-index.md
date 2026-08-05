# 符号索引

## 目标
提供类、方法、函数与反向调用查询的保守候选。

## 输入
source-index、当前 PHP 文件和项目标识。

## 执行步骤
识别 namespace/class/interface/trait/extends/implements/function/method/visibility 与行范围，解析参数的完整限定类型，附哈希，保存 calls/called_by/tables/routes/modules。

## 输出
项目独立 symbol-index JSONL；复杂动态语法附 `PARSER_LIMITATION`。

## 质量检查
检查每个符号行范围和文件哈希，随机对照源码；同名短类不能覆盖完整参数类型。symbol manifest 的 parser_version 变化时重建 PHP 符号，禁止复用旧解析结果或宣称完整 PHP AST 精度。

## 失败处理
解析异常降级为 `PARTIAL`，列出无法解析语法，不中断其他文件。
