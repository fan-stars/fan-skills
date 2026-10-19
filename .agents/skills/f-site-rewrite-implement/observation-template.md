# Playwright 观测记录模板

```markdown
# Observation: <siteId> / <pageOrModule>

- datetime:
- baseUrl:
- path:
- viewport:
- env: legacy | reference | rewrite
- auth: none | cookie | login（勿记录密钥值）

## Structure / IA
- 首屏/模块区块（自上而下）:
- 导航项:
- 本模块标题 / 副文案:
- 对齐与间距节奏（左缘/栏间距是否均匀）:

## Interactions
- 可点击 / Tab / 轮播等:
- Hover（如有）:
- 激活 / 选中态（如有）:
- 角标（如有：文案、位置、色）:
- 动效（如有）:
- 焦点 / 禁用 / 加载 / 空态（如有）:

## Data clues
- 空态 / 加载态:
- 可见 API 名（如有）:

## Chrome 抽样（供 ≥95% 评分）
| 项 | 值（legacy / reference） |
| --- | --- |
| 字体 font / size / weight / line-height / color | |
| 背景 background | |
| 边距 margin / padding / gap | |
| 大小 width / height | |
| 边框 / 分割线 border | |
| 圆角 border-radius | |
| 阴影 / 层级 box-shadow / z-index | |
| 主色 / 状态色 | |
| 图标 / 图片尺寸与 object-fit | |
| Hover（如有） | |
| 激活 / 选中态（如有） | |
| 角标（如有） | |
| 动效 transition/animation（如有） | |
| 透明度 / 叠层（如有） | |
| 滚动与溢出 / line-clamp（如有） | |
| 内容区 max-width / 水平 padding | |

## Screenshots
- path:
- hover / 激活态截图（如有）:

## Diff notes
- vs legacy:
- vs reference:
- vs rewrite:
```
