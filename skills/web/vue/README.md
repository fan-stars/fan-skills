# Web / Vue

Vue、Nuxt 与 Vben Admin 相关 skills

> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。

## 总览

| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |
| --- | --- | --- | --- | --- |
| `nuxt` | `skills/web/vue/nuxt/` | Nuxt 4 全栈 Vue：目录约定、路由、数据获取、模块与混合渲染。 | [skills.sh](https://skills.sh/antfu/skills/nuxt) | [GitHub](https://github.com/antfu/skills/blob/main/skills/nuxt/SKILL.md) |
| `vben` | `skills/web/vue/vben/` | Vben Admin 5.0 中后台开发：Vue3、Vite、路由权限与 Monorepo 约定。 | [skills.sh](https://skills.sh/vbenjs/skills/vben) | [GitHub](https://github.com/vbenjs/skills/blob/main/skills/SKILL.md) |

## 详细介绍

### `nuxt`

**路径**：`skills/web/vue/nuxt/`

#### 核心能力

提供 Nuxt 4.x 权威向参考：`app/` srcDir、文件路由、useFetch/useAsyncData、中间件、Nitro 服务端、模块与混合渲染部署等，并链到细分 references。

#### 适用场景

开发或改造 Nuxt 应用、写 server routes、配置 SSR/混合渲染、排查自动导入与别名问题时使用。

#### 主要覆盖内容

目录与别名、nuxt.config、CLI、路由、数据获取、模块、部署等核心主题索引（基于 Nuxt 4，默认 srcDir 为 app/）。

#### 注意事项

`~`/`@` 指向 `app/`，根目录用 `~~`/`@@`。细节以 references 为准；勿按 Nuxt 2/3 旧目录假设落文件。

### `vben`

**路径**：`skills/web/vue/vben/`

#### 核心能力

指导在 Vben 5 Monorepo 中开发 Ant Design Vue / Element Plus / Naive 应用：路由菜单 meta、权限模式、请求与状态、常用 pnpm 脚本。

#### 适用场景

基于 Vben Admin 5 做中后台页面、权限路由、多 UI 库应用或 mock 联调时使用。

#### 主要覆盖内容

apps/packages 结构、dev/build 命令、路由模块写法、权限与布局相关核心指南。

#### 注意事项

按实际选用的 UI 应用（antd/ele/naive）启动对应脚本。路由 meta 字段需与框架约定一致，勿混用旧版 Vben 结构。
