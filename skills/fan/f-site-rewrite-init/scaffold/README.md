# site-rewrite（骨架说明）

本目录是 **`f-site-rewrite-init` skill 内的 scaffold 模板**。

- **分发**：随 skill 拷贝到任意仓库  
- **使用**：执行 init 时复制到**项目根**的 `site-rewrite/`，再填写配置  
- **不要**在业务仓库里只提交空的 `site-rewrite/` 却不装 skill——新项目应装 skill 后由 init 生成  

| 路径 | 用途 |
| --- | --- |
| `refactor.config.yaml` | 前台站、数据接口、源码树、框架 / UI 库（无密钥） |
| `secrets.local.env.example` | 密钥占位；本地复制为 `secrets.local.env` |
| `indexes/` | 已读源码 / 观测 / 模块 / skills / 数据接口目录 |
| `data-apis/` | 接口 URL、请求参数、响应字段（脱敏） |
| `observations/` / `matches/` / `playbooks/` | 观测、评分、过程与踩坑 |

配套 skill：`f-site-rewrite-implement`。打包说明见上级 `PACKAGING.md`。
