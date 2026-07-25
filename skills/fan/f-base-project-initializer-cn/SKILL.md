---
name: f-base-project-initializer-cn
description: 从固定的 fan-base 与 fan-base-vben Gitee 仓库初始化并重命名 Fan 全栈项目。用于用户希望基于模板创建新 Fan 项目、重命名前后端目录、迁移 Maven 坐标和数据库名、生成运行脚本或验证项目能否启动的场景。
---

# Fan 项目初始化（中文）

从以下固定模板初始化新项目：

- `git@gitee.com:fan-stars/fan-base.git`
- `git@gitee.com:fan-stars/fan-base-vben.git`

## 必需输入

修改文件前，先从用户处获得目标项目名称。将名称规范化为小写短横线格式；如果规范化结果与用户输入不同，说明变化并进行确认。

派生以下变量：

```text
PROJECT_NAME=<用户输入的项目名>       # 示例：fan-idc
BACKEND_DIR=$PROJECT_NAME            # fan-idc
FRONTEND_DIR=$PROJECT_NAME-vben      # fan-idc-vben
MAVEN_GROUP_ID=cn.fanstars.$PROJECT_NAME
DATABASE_NAME=${PROJECT_NAME//-/_}   # fan_idc
```

用户未指定目标位置时，使用当前工作区作为目标目录。目标目录已存在且非空时，不得覆盖。

## 执行流程

跟踪并报告以下阶段：

```text
- [ ] 确认名称与目标目录
- [ ] 拉取两个模板仓库
- [ ] 重命名目录并配置远程
- [ ] 更新后端 Maven 坐标
- [ ] 更新数据库及相关配置
- [ ] 检查并处理残留模板名称
- [ ] 清理并构建后端
- [ ] 在可用时生成根目录运行脚本
- [ ] 在可用时生成根目录 AGENTS.md
- [ ] 启动并验证可运行的应用
```

### 1. 拉取并重命名

先将两个仓库拉取到临时模板目录，再分别重命名为 `BACKEND_DIR` 和 `FRONTEND_DIR`。

对两个仓库都执行：

1. 将远程 `origin` 重命名为 `fan-base`。
2. 解除当前分支的上游关联，等待以后确定目标远程。
3. 除非用户提供目标远程，否则不得推送或新建远程。

### 2. 更新 Maven 坐标

遵守以下不变量：

- 根父项目：
  - `groupId` = `MAVEN_GROUP_ID`
  - `artifactId` = `PROJECT_NAME`
- 可执行模块保持为 `fan-server`：
  - 目录保持为 `fan-server/`
  - 模块 `artifactId` 保持为 `fan-server`
  - 输出文件保持为 `fan-server.jar`

对所有受版本控制的 `pom.xml` 执行坐标迁移：

1. 将内部 `cn.fanstars.base` groupId 替换为 `MAVEN_GROUP_ID`。
2. 将根项目及父项目引用中的 `fan-base` 替换为 `PROJECT_NAME`。
3. 保留外部依赖的 groupId。
4. 除根父项目的 artifactId 外，保留所有模块的 artifactId。

完成机械替换后检查差异，尤其确认：

```xml
<!-- 根 pom.xml -->
<groupId>cn.fanstars.<project-name></groupId>
<artifactId><project-name></artifactId>

<!-- fan-server/pom.xml -->
<parent>
  <groupId>cn.fanstars.<project-name></groupId>
  <artifactId><project-name></artifactId>
</parent>
<artifactId>fan-server</artifactId>
```

### 3. 更新数据库及相关名称

将模板数据库名 `fan_base` 替换为 `DATABASE_NAME`，检查范围包括：

- `fan-server/src/main/resources/application-local.yaml`
- `fan-server/src/main/resources/application-dev.yaml`
- 相关 SQL 注释、初始化脚本、Docker 文件和文档

更新 Docker 默认值：

- `container_name` 改为 `PROJECT_NAME`
- `--spring.application.name` 改为 `PROJECT_NAME`

未经明确授权，不得创建、重命名、复制或删除真实数据库。如果启动时出现 `Unknown database`，提示用户创建数据库，或者请求数据库迁移授权。

### 4. 检查模板名称残留

在受版本控制的源文件与配置文件中搜索：

```text
fan-base
fan_base
cn.fanstars.base
```

排除 `.git`、构建产物、依赖目录、运行日志和缓存。修改前先判断每个匹配项的用途：

- 更新项目标识、内部 Maven 坐标、数据库名、Docker 名称以及当前文档。
- 用户未提供目标远程时，保留模板远程 URL 和远程名称。
- 不要盲目改写无关的历史文本或第三方标识。

### 5. 验证后端

在后端仓库根目录执行：

```bash
mvn clean
mvn -pl fan-server -am package -DskipTests
```

两个命令都必须成功，并确认以下产物存在：

```text
fan-server/target/fan-server.jar
```

### 6. 生成运行脚本

如果 `$project-runtime-manager` 可用，在完成目录重命名和配置迁移后调用它：

1. 从重命名后的路径重新识别后端与前端。
2. 在工作区根目录的 `scripts/` 中生成统一运行管理文件，不得放入任一子项目。
3. 确认生成的脚本引用 `BACKEND_DIR`、`FRONTEND_DIR` 和 `fan-server.jar`。
4. 将本地运行覆盖配置放在根目录 `scripts/config/`。
5. 不得覆盖两个仓库中已有的 `scripts/` 内容。

如果该 Skill 不可用，说明情况；除非用户明确要求后备实现，否则不自行生成替代脚本。

### 7. 生成根目录 AGENTS.md

如果 `$create-agentsmd` 可用，在两个项目和运行脚本达到最终结构后调用它：

1. 在工作区根目录创建一份统一的 `AGENTS.md`，不得放入任一子项目，除非用户明确要求嵌套文件。
2. 写入文档前，检查真实的后端与前端构建、测试、开发和运行命令。
3. 记录以下上游关系：
   - 后端基于 `https://gitee.com/zhijiantianya/ruoyi-vue-pro`
   - Vben 前端基于 `https://gitee.com/yudaocode/yudao-ui-admin-vben`
4. 将两个 `fan-base` 远程标记为只读模板来源。禁止推送、创建远程分支或标签、创建合并请求，以及设置当前分支跟踪它们。
5. 允许项目专属的本地修改；但如果用户请求的修改属于公共模板或应在 `fan-base` 修复，停止该公共部分，向用户说明涉及的模板、文件和建议方案。由用户修改对应的 `fan-base` 项目，确认后再继续。
6. 说明设置目标远程或执行任何远程变更都需要用户明确授权。
7. 写入最终目录名、Maven 坐标不变量、数据库安全边界、根目录运行脚本、外置配置路径、测试命令和交付检查。
8. 根据 `$project-runtime-manager` 加入强制性的编码期配置规则：
   - 开发功能或修复代码时，不得修改项目已有配置文件，包括 `application*.yml|yaml`、`bootstrap*.yml|yaml`、`.env*`、`package.json`、`vite.config.*`、`nuxt.config.*`、`pom.xml`、`build.gradle*` 和 `settings.gradle*`。
   - 只能只读现有项目配置，用于推断运行参数。
   - 运行参数只能写入 `$project-runtime-manager` 定义的工作区根目录 `scripts/config/`，并由根目录启动脚本通过 CLI 参数或环境变量加载。
   - 已有合适的 `scripts/config/` 文件时，不得另建第二套配置约定。
   - 如果需求确实涉及依赖、构建或共享项目配置，且无法用运行时外置配置表达，修改前先停止并向用户说明必须修改的文件及原因。
   - 明确该编码期规则不阻止本初始化 Skill 前面执行的一次性项目标识迁移。

如果根目录已有 `AGENTS.md`，先检查内容，只补充缺失或过时的项目说明，并保留用户编写的无关规则。

如果 `$create-agentsmd` 不可用，说明情况；除非用户明确要求，否则不自行生成替代文件。

### 8. 启动并验证

根目录启动脚本存在时：

1. 使用这些脚本启动后端和前端。
2. 保持进程运行足够时间，以捕获延迟出现的初始化错误。
3. 执行状态检查脚本。
4. 根据识别出的 HTTP 端口发起本地请求进行验证。
5. 如果进程最初显示成功但随后退出，检查运行日志。

只有进程检查和 HTTP 检查同时通过，才判定启动成功。应用响应正文为 `401`、但 HTTP 状态码为 `200` 时，可视为后端和鉴权链已经正常运行。

如果 Bouncy Castle/JCE 校验失败，优先通过根目录外部运行配置改用标准 JDK。如果打包内置的安全提供程序仍然失败，先说明行为变化，再使用同步的前后端本地覆盖配置；不得仅为掩盖错误而修改仓库内的应用配置。

## 完成报告

报告以下内容：

1. 最终前后端目录名称
2. 根 Maven 坐标，以及保持不变的 `fan-server` 模块坐标
3. 数据库名称，以及是否操作过真实数据库
4. 已修改的文件或类别
5. 清理和构建结果
6. 运行脚本位置
7. 根目录 AGENTS.md 位置，以及记录的上游和远程保护规则
8. 进程 ID、端口和 HTTP 验证结果
9. 仍保留的模板标识及其保留原因
