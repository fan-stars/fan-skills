# 测试

Web 应用自动化测试

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `webapp-testing` | `skills/testing/webapp-testing/` | 用 Playwright 与辅助脚本测试本地 Web 应用：交互、截图与日志。 | [skills.sh](https://skills.sh/anthropics/skills/webapp-testing) | [GitHub](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) |

## 详细介绍

### `webapp-testing`

**路径**：`skills/testing/webapp-testing/`

#### 核心能力

编写原生 Python Playwright 脚本验证前端行为；用 with_server 管理服务生命周期；先侦察 DOM/截图再定位选择器执行操作。

#### 适用场景

需要验证本地前端功能、调试交互异常、捕获页面截图，或查看浏览器控制台日志以定位问题时使用。

#### 主要覆盖内容

静态 HTML vs 动态应用决策树、服务器已启动/未启动分支、with_server 用法与脚本优先 `--help` 的约定。

#### 注意事项

先跑脚本 `--help`，勿一上来通读巨大脚本源码。选择器应来自实际渲染结果，避免臆造。
