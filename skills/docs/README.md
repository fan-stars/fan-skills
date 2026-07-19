# 文档与办公

Word、PDF、PPT、表格处理

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `docx` | `skills/docs/docx/` | 创建、编辑、读取 Word 文档与模板，处理版式、修订、图片与内容重组。 | [skills.sh](https://skills.sh/anthropics/skills/docx) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/docx/SKILL.md) |
| `pdf` | `skills/docs/pdf/` | 处理 PDF：读写提取、合并拆分、表单、水印、加密与 OCR 等全套操作。 | [skills.sh](https://skills.sh/anthropics/skills/pdf) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/pdf/SKILL.md) |
| `pptx` | `skills/docs/pptx/` | 创建、编辑与分析 PowerPoint：新建幻灯片、改模板、抽取与校验。 | [skills.sh](https://skills.sh/anthropics/skills/pptx) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md) |
| `xlsx` | `skills/docs/xlsx/` | 创建与编辑电子表格：公式、格式、清洗数据及 csv/tsv 与 xlsx 互转。 | [skills.sh](https://skills.sh/anthropics/skills/xlsx) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/xlsx/SKILL.md) |

## 详细介绍

### `docx`

**路径**：`skills/docs/docx/`

#### 核心能力

用 docx-js 新建专业 .docx/.dotx；用解压改 XML 编辑已有文档；用 pandoc 提取内容。覆盖目录、页眉页脚、表格、列表、图片、批注与修订等常见办公排版需求。

#### 适用场景

用户要报告、备忘录、信函、模板等 Word 交付物，或对现有 .docx/.dotx 做抽取、替换、插图、重组时使用。不用于 PDF/表格/谷歌文档。

#### 主要覆盖内容

创建脚本当注意的页尺寸、横向、表格双宽度、底纹、编号、分页与 TOC 等陷阱；编辑路径与读取路径分流。

#### 注意事项

docx-js 不能可靠打开再编辑已有文件，编辑请走 unzip/XML。勿把 PDF 或电子表格任务误用本 skill。

### `pdf`

**路径**：`skills/docs/pdf/`

#### 核心能力

用 pypdf 等库与命令行完成文本/表格提取、合并拆分、旋转、水印、新建 PDF、填表、加解密、抽图与扫描件 OCR，复杂场景见 REFERENCE/FORMS。

#### 适用场景

用户提到 .pdf、需要从 PDF 提取内容、合并拆分页面，或生成/加密/填表/OCR 等任何 PDF 加工请求时启用。

#### 主要覆盖内容

Quick start 与 pypdf 合并拆分、元数据与旋转；表单见 FORMS.md，进阶特性与更多示例见 REFERENCE.md 索引。

#### 注意事项

填表先读 FORMS.md。扫描件需 OCR 才能检索；大文件注意内存与逐页处理。

### `pptx`

**路径**：`skills/docs/pptx/`

#### 核心能力

用 pptxgenjs 新建演示文稿；解压改 XML 编辑已有/模板；用 markitdown 与缩略图脚本阅读；提供加页、清理与校验脚本。

#### 适用场景

涉及 .pptx/.potx、deck/slides/presentation 的创建、修改、合并拆分或内容抽取时使用。

#### 主要覆盖内容

创建陷阱、编辑工作流、thumbnail/add_slide/clean/validate 等脚本职责。

#### 注意事项

从模板派生的文件校验需传 `--original`。编辑后保持关系与内容类型一致，避免手工漏改 rels。

### `xlsx`

**路径**：`skills/docs/xlsx/`

#### 核心能力

用 openpyxl 做带公式与格式的创建编辑，用 pandas 做批量读写，用 markitdown 快速预览；强调公式可重算、专业字体与零公式错误。

#### 适用场景

以 xlsx/xlsm/csv/tsv 为主要输入或交付物、清洗畸形表、按用户列名与公式规格出表时使用。

#### 主要覆盖内容

工具选型表、输出质量要求、公式与值双次加载等常见陷阱；配套 recalc 等脚本。

#### 注意事项

交付物必须是表格文件。用公式而非写死结果；严格遵循用户给定的表名与列头。Word/HTML 主交付勿用本 skill。
