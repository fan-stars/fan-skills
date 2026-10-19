# site-rewrite indexes

Agent **必须**在阅读源码 / 示例 / 写入观测 / 探测数据接口后更新 `site-rewrite/indexes/`，供下次快速定位。

## 文件

| 文件 | 用途 |
| --- | --- |
| `sources-read.yaml` | 已阅读的旧站源码路径、模块、要点摘要 |
| `examples-read.yaml` | 已阅读的示例项目路径与用途 |
| `observations-index.yaml` | observations/ 下文件目录 |
| `modules.yaml` | 模块切片、状态、最近 match 分 |
| `skills-planned.yaml` | 本轮必用 / 按需 / 不适用的 skills |
| `data-api-calls.yaml` | 已请求过的数据接口目录（详情在 `data-apis/`） |

## 更新时机

| 动作 | 更新 |
| --- | --- |
| 读完一个源码文件/目录 | append `sources-read.yaml` |
| 读完示例 | append `examples-read.yaml` |
| 新建观测 md/截图 | append `observations-index.yaml` |
| 模块对比通过/失败 | 更新 `modules.yaml` |
| 第 5 步分析 skills | 写入 `skills-planned.yaml`；必用项 `read: true` |
| 请求或观察到数据接口 | 写 `data-apis/*.md` + append `data-api-calls.yaml` |

## 速查流程（implement 开头）

1. 读 `refactor.config.yaml`（含 `dataApis`）  
2. 读 `indexes/modules.yaml`、`sources-read.yaml`、`data-api-calls.yaml`  
3. 若索引已有本模块 / 本 path 条目 → **先打开索引中的 path / recordFile**，再按需补读或补请求  
4. 新内容写回索引（去重：同一 `path` 或同一 `apiId+method+path` 更新 `lastRead` / `lastCalled`）

## 数据接口记录规则

- 配置：`dataApis[]`（名称：**数据接口**）  
- 详情：`site-rewrite/data-apis/`（模板见 skill 内 `data-api-record-template.md`）  
- 目录：`indexes/data-api-calls.yaml`  
- 记录内容：完整 URL 形态、请求参数（query/body 字段）、响应字段结构与脱敏样例  
- **严禁**写入 token / cookie / 密码 / 隐私明文  

字段形状见仓库 `site-rewrite/indexes/*.yaml` 头注释。
