# AI Skill 说明生成协议

本文件定义同步流程中 AI 生成中文说明的数据结构与质量标准。  
生成结果写入 `generated/skill-docs.json`（派生产物，非 catalog）。

## 输入事实源

对每个 skill，AI **必须**：

1. 读取 `.agents/skills/<name>/SKILL.md`
2. 若正文引用 `references/`、`rules/` 等本地文件且对理解能力边界有必要，再按需读取
3. **禁止**仅凭 skill 名称、`skills-catalog.json` 链接或旧简介臆测能力

## 输出结构（每个 skill）

```json
{
  "contentHash": "<skill 源目录内容哈希>",
  "summary": "一段中文短简介，用于表格「简介」列",
  "capabilities": "核心能力（中文段落或条目）",
  "scenarios": "适用场景（中文）",
  "coverage": "主要覆盖内容（中文）",
  "notes": "使用或选型注意事项（中文）"
}
```

文件顶层：

```json
{
  "version": 1,
  "skills": {
    "<skill-name>": { "...见上..." }
  }
}
```

## 质量标准（脚本强制校验）

| 字段 | 要求 |
| --- | --- |
| `contentHash` | 非空；须与当前源目录哈希一致才算有效 |
| `summary` | 非空中文；长度 ≥ 24；不含 `|`（表格安全） |
| `capabilities` | 非空中文；长度 ≥ 40 |
| `scenarios` | 非空中文；长度 ≥ 40 |
| `coverage` | 非空中文；长度 ≥ 40 |
| `notes` | 非空中文；长度 ≥ 40 |

「中文」：至少包含一个 CJK 统一汉字。

## 缓存与失效

- 源目录内容哈希未变 → 复用已有生成结果  
- 哈希变化 / 缺失 / 字段校验失败 → 必须重新生成，不得用于渲染  

## 渲染到 README

分类 README：

1. 表格总览：名称、路径、`summary`、skills.sh、GitHub  
2. 每个 skill 一节 `### \`name\``，含四个小节：核心能力、适用场景、主要覆盖内容、注意事项  
