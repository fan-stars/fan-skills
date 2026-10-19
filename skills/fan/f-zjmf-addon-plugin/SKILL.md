---
name: f-zjmf-addon-plugin
description: Use when creating, renaming, or changing a ZJMF 3.5.8 addon in fan-zjmf-dir, including a new self-built plugin name, an Ant Design admin page that does not match fan_dcimcloud_os_group, pagination showing "20 / page", a short table whose horizontal bar sits mid-card, a clicked button with no spinner beside its label, CLI install querying shd_plugin_model, an addon URL returning 您还没有登录 and replacing the admin PHP session, PHP 7.2 formatting, plugin CSS, a test-site deploy, a jsonrule page that toasts SUCCESS while the row still shows the old comparison, a supplier list whose only action is a link, a filter bar that also holds profit or navigation fields, a table whose empty text is "No data", rsync as www failing with Permission denied on a symlink under /root, or a deleted plugin file still present on the test site after rsync.
---

# ZJMF Addon 插件

先读工作区 `AGENTS.md`。它管 Git、Java 工具仓库和参考库边界。本技能管插件叶子目录里的实现。开发只写 `fan-zjmf-manger-decoded/public/plugins/<类型>/<插件名>/`。参考 ZIP 只读，在 `/tmp` 解压后不执行其中的 PHP。不改 `app/`、根 `vendor/`、主题、`behavior/`。官网示例和本地 `demo_style`、`Plugin.php`、`PluginModel.php` 不一致时，以本地 3.5.8 源码为准。

## 命名

此后**新建的自研插件**目录必须是小写 snake_case，且以 `fan_` 开头，例如 `addons/fan_os_sync`，命名空间 `addons\fan_os_sync`。`$info['name']` 与类名是对应的 StudlyCase，并以 `Fan` 开头。PHP 命名空间不能含连字符，所以不用 `fan-` 做目录名。

已有插件保持原目录，除非这次任务就是改名。`fan_dcimcloud_os_group` 已经完成改名。业务表仍是 `addon_dcimcloud_os_*`，改目录时不要改表名，也不要 `DROP TABLE`。

入口文件是 `{Studly}Plugin.php`。框架用类名去掉末尾 6 个字符 `Plugin` 得到 `$info['name']`，这个名字必须和 `$info['name']` 一致。菜单写成 `FanDcimcloudOsGroup://AdminIndex/index`。浏览器参数 `_plugin` 是 `fan_dcimcloud_os_group`。测试站上只复制新目录不够：要先卸载旧插件名，再安装新名字。本插件 `uninstall()` 只返回 true，不删表；`install()` 是 `CREATE TABLE IF NOT EXISTS`。卸载旧名时类可以已经不在，注册行仍会删掉；安装新名时新类文件必须已经在新目录。

| 借口 | 事实 |
| --- | --- |
| snake_case 就够了，不必加前缀 | 自研插件没有 `fan_` 就不算按本约定命名 |
| 这次顺手把旧插件改成 `fan_` | 改名单独授权，不同任务不改目录 |
| 目录直接写 `fan-` | 连字符破坏命名空间，目录用 `fan_` |
| 改名后只复制文件 | 后台插件记录仍是旧名字，要卸载旧名再安装新名 |
| 给表格 `overflow-x: hidden` 去掉横条 | 另一轴变成可滚动，表内出现竖条 |
| 用 `!important` 把表头居中 | 表头写单元格 `textAlign: 'center'`，正文仍由列 `align` 决定 |
| `response.ok` 就是成功 | `jsonrule()` 失败也是 HTTP 200，成败只看正文 `status` |
| 成功提示用外壳 `msg` | 外壳 `msg` 常是通用成功文案；同步说明在 `data.msg`，`data.data.sync_status === 'partial'` 仍要显示 |
| 对比对象留着，刷新列表就够了 | 行优先显示内存对比时，同步成功后要删掉该商品的缓存，否则下次仍提交旧指纹 |
| 写了 `height:100%` 和 `scroll.y` 就算铺满 | 壳层没按视口设高度时，表体仍矮，横条停在卡片中部。对照下面的主表清单 |
| 分页能显示条数就行，英文 `20 / page` 可以 | `antd.min.js` 没有语言包。不提供 locale 回退，分页就是英文 |
| 列上写了 `width` 就不用写到单元格 | `scroll.y` 拆成表头、表体两张表，列宽必须同时进 `onCell` 和 `onHeaderCell` |
| 文件拷到测试站就是装好了 | 拷文件不插 `shd_plugin`，也不建表。`install()` 只建表 |
| 用 `new PluginModel()` 就能插入插件行 | CLI 未加载 `class_suffix` 时，模型表名是 `shd_plugin_model`。插入用 `Db::name('plugin')` |
| 打开插件地址就能测页面 | 未登录时正文是 `{"status":405,"msg":"您还没有登录"}`，并 `Set-Cookie` 换掉原会话，把已登录的浏览器打回登录页 |
| 表格已经有 loading，按钮不用转 | 表格遮罩盖不住筛选条。发请求的按钮在请求期间写 `loading`，转圈在按钮文字左侧 |
| 用整页 Spin、`message.loading` 或 `layer.load` 当 loading 框 | 现有 Ant 插件不用 Layui。对照 `fan_product_desc_sync` 的查询按钮 |
| 一个 busy 加到每一行每个按钮 | 只让当前行、当前动作的按钮转。跳转链接不加 `loading` |
| 单独做一页供应商，上面只有「同步」链接 | 选择放在主表上。默认不选，选中后才请求。连接状态不是 1 的项留在选项里并禁用。列表页不要逐个登录上游 |
| 利润、分组、前台导航放在筛选条，少点一次 | 筛选条只放查询。这些写入条件放进动作按钮打开的弹框。没选中行就不要打开弹框 |
| 读 `shd_nav` 且 `nav_type=2` 就是前台导航 | 与商品编辑页相同，用 `Menu::getOneNavs('client')` 里 `nav_type==2`。官网头部外链不算。挂载结果在启用菜单的 `nav_list`，`shd_nav.relid` 经常是空的 |
| 空表留着英文 No data | `Table` 写 `locale.emptyText`。还没选择时用「请选择…」并且不发列表请求；选中后没有行才用「暂无数据」 |
| 同一轮点击里 setState 之后马上读 state | 加载函数接收这次的新值。这一帧的 state 仍是旧值 |
| antd 6 弹框用 `destroyOnClose` 或 `bodyStyle` | 用 `destroyOnHidden` 和 `styles.body`。`className` 用插件自己的弹层类 |
| 测试站就是解码版 3.5.8 | 先读测试站 `version`。核心是 ionCube 时不改它。上游请求优先用运行中的 `zjmfCurl`。解码版没有的分支不要写进 `app/` |
| `www` 走工作区软链就能部署 | `www` 进不了 `/root`。`runuser -u www` 的目标必须是 `/www/wwwroot/idc-test-dir/idc-test/public/plugins/...` |
| 源文件删了，不加 `--delete` 就清不掉测试站旧文件 | 仍然禁止目录级 `--delete`。部署后用 `www` 只删除目标上那一个已删除路径 |

## 类型

| 类型 | 运行目录 | 参考 ZIP |
| --- | --- | --- |
| 扩展 | `addons/<plugin>` | `plugins/addon/*.zip` |
| 支付 | `gateways/<plugin>` | `plugins/gateway/*.zip` |
| 认证 | `certification/<plugin>` | `plugins/certification/*.zip` |
| 邮件 | `mail/<plugin>` | `plugins/mail/*.zip` |
| 短信 | `sms/<plugin>` | `plugins/sms/*.zip` |
| 服务器 | `servers/<plugin>` | `plugins/server/*.zip` |
| 登录 | `oauth/<plugin>` | 参考库无此分类 |

参考路径是单数 `addon`、`gateway`、`server`。先看压缩包里的目录名再映射。服务器模块用 `<plugin>/<plugin>.php` 函数 API。OAuth 不继承现代插件基类。支付、认证、短信、邮件、服务器回调要验签名、订单、金额和状态，并且幂等。

自研插件的 `fan_` 前缀用于 `addons`、`gateways`、`certification`、`mail`、`sms` 的新建目录。既有 Layui 插件继续 Layui，不在里面新开 Ant Design 页。`config.php` 表单、前台 `clientarea`、`servers`、`oauth` 不套用下面的 Ant Design 页约定。

## 界面

新的自定义后台页用钉死版本的 React 18、dayjs、`antd.min.js`（起点 `react@18.3.1`、`react-dom@18.3.1`、`dayjs@1.11.13`、`antd@6.6.3`）。`createRoot` + `ConfigProvider` 默认 Token + `antd.App`。`cssVar.key` 用本插件自己的名字，新插件不复用 `dcog`。不加载 `antd/dist/reset.css`，不把 `antd.css` 放进页面或 `assets/`，不在插件里做前端构建。组件样式只来自 `antd.min.js` 的运行时注入。请求用同源 `fetch`，POST 为 `application/x-www-form-urlencoded`。`jsonrule()` 失败也是 HTTP 200，正文 `status !== 200` 才是失败。成功提示读内层 `data.msg`；`sync_status === 'partial'` 仍要显示。同步成功后删掉该商品的内存对比。列表总数沿用 `data.sum` 这类现有字段。确认框 `onOk` 读 ref，不读打开确认时那一帧的 state。

已有 Layui 插件继续 Layui，不在其中新开 Ant Design 页。

写新的主表页之前，先打开 `addons/fan_dcimcloud_os_group/template/admin/logs.tpl`、`assets/dcog.css`、`assets/dcog-antd.js` 里的 `dcogAntdCol` 和 `dcogAntdLocale`。用本插件自己的类名重做同一骨架，不要另起一套更薄的布局，也不要复用 `dcog` 这个 `cssVar.key`。

主表页同时满足这些，缺一条就不算对齐：

- 根类名是 `{前缀} {前缀}-antd`，例如 `fdct fdct-antd`。挂载后按壳层 `getBoundingClientRect().top` 把根高度写成 `window.innerHeight - top`，最小 360。
- 内容是一张 `Card`（`bordered: false`），外层 `{前缀}-page-fill`，表在 `{前缀}-table-fill` 里。CSS 高度链、绝对铺满和分页贴底按 `dcog.css` 的对应规则改类名，不改 `html` 字号。
- `scroll.y` 用填充层的客户区高度减去表头和分页，不拿根节点顶距再减一个常数冒充。
- `ConfigProvider` 传入 locale。`antd.min.js` 没有语言包时，页面自己提供中文回退，分页单位是「条/页」。总数文案是「第 n-n 条/总共 n 条」。不改用 `antd-with-locales.min.js`。
- 列同时有 `width`、`minWidth`，并且 `onCell` 与 `onHeaderCell` 都带上同一 `minWidth`。表头 `textAlign: 'center'` 且不换行。表密度用 `size: 'middle'`。
- 状态是带颜色的 `Tag`。筛选放在卡片内，控件有最小宽度。改了本插件 CSS 或 JS 后，模板里的 `?v=` 一起改。
- 会请求后端的按钮在请求期间设置 `loading`，转圈在文字左侧。查询用列表请求的那个布尔。行内刷新、重置、详情只用「动作:行 id」。确认框 `onOk` 返回 Promise，确认按钮才会转。纯跳转按钮不加 `loading`。

自有 CSS 只留两件套：上面这条高度链，以及插件根和弹层类名上抵消管理壳 `button:focus` 粗描边，保留 `:focus-visible`。

表头居中写在表头单元格样式（`textAlign: 'center'`，不换行），不写整表 `!important`。列同时写 `width` 和 `minWidth`。编号、状态、数量、操作的正文居中。商品名是单行链接，指向 `/{后台路径}/#/edit-product?id=`，不换行。错误和诊断明细左对齐并换行。状态用 `Tag`。行内操作使用小号 `Button`；对比、查看、重新对比都用 `type="primary"`；核心同步等危险操作使用 `danger`。主表需要横向最小列宽时 `scroll.x` 为 `max-content`。只有一张表要吃满后台内容区时才用视口剩余高度和 `scroll.y`。弹层 `centered`，内容区 `maxHeight: calc(100vh - 180px)`，只纵向滚动，关闭后销毁；弹层里的表不再自带横条或竖条。`Descriptions` 标签列固定宽度不换行。筛选控件设最小宽度。分页显示当前区间和总条数。不可信字段用文本节点，不拼接 HTML。`getPopupContainer` 可以返回 `document.body`，避免卡片裁切下拉。

需要排序的列才加排序。分页列表用服务端白名单排序，不在当前页里假排序。比对弹框只让弹框内容区纵向滚动，长文本换行。`Row` 横向 gutter 会出负外边距，弹框内横向间距用 0。这些约定也适用于把已有自定义后台页改成 Ant Design。复杂列可以看 `addons/fan_dcimcloud_os_group`，但不要复用它的 `cssVar.key` `dcog`，也不要把它的 `scroll.y` 铺满当成每个新页面的必选项。

CDN 加载失败时在挂载根显示错误。同步日志的操作列用中文标签，不要直接显示 `sync`：`sync` 同步、`compare` 比对、`assign` 关联、`refresh` 刷新。

入口页就是主表。改 `index()` 渲染的模板即可，不为跳转再加菜单项，也不为换页面重装插件。主表依赖上游、供应商或同类选择时，下拉默认空，选中后才请求；清空选择就清空表格。筛选条只留查询条件。利润、本地分组、前台导航这类写入条件放进「导入」或对应动作打开的弹框，弹框里说明这次会写入的范围。没选中行时不打开弹框，在页面上提示先选择。

前台导航选项与后台添加商品相同：`(new \app\common\logic\Menu())->getOneNavs('client', null)` 里 `nav_type == 2`。不要用 `nav` 表代替启用中的会员中心菜单，也不要把官网头部、底部菜单算进去。导入之后到 `menus.nav_list` 里核对商品 id，不要只看 `nav.relid`。

`Table` 必须有中文 `locale.emptyText`。未选择依赖项时表格不发列表请求。antd 6 的 `Modal` 使用 `centered`、`destroyOnHidden`、`styles.body.maxHeight = calc(100vh - 180px)`、`styles.body.overflowY = auto`。下拉 `getPopupContainer` 返回 `document.body`。

弹框默认挂到 `document.body`，写在 `.dcog` 里的选择器盖不到它。要限制弹框时给 `Modal` 加插件自己的 `className`。消横向滚动时不要给表格写 `overflow-x: hidden`：另一轴会变成可滚动，表内再长出竖条。只让弹框内容区 `overflowY: auto`、`overflowX: hidden`。改了 `dcog.css` 或 `dcog-antd.js` 后，四页模板里的 `?v=` 要一起改，否则测试站继续用旧文件。

## PHP 与格式

PHP 7.2.33：禁止 typed properties、箭头函数、union、`match`、nullsafe。自有 PHP 用 `array()` 和 4 空格。格式化程序是工作区 `script/php-cs-fixer/php-cs-fixer-2.19.phar`（本机没有 PHP 7.4，不能跑 php-cs-fixer 3）。规则文件放在插件内，`setUsingCache(false)`，只扫该插件 `.php`。模板脚本和插件 JS 保持 ES5，用 `node --check`，不用会改语法的 Prettier。不格式化 jsDelivr 库和第三方 `vendor/`。

新写 PHP 在提交前用该 phar 跑 dry-run。2.19 没有 `--path-mode`。配置必须 `setUsingCache(false)`，否则会在当前目录留下 `.php_cs.cache`。

```bash
php script/php-cs-fixer/php-cs-fixer-2.19.phar fix "$plugin_dir" --config="$plugin_dir/.php-cs-fixer.dist.php" --dry-run --diff
```

安装迁移增量、幂等，不以 `DROP TABLE` 开始，不写死 `shd_` 前缀。静态检查不要调用 `install()`、`uninstall()` 或支付、短信、认证接口。卸载保留业务数据。

测试替身不要继承会走自动加载的生产类。PHP 不会把这种子类提前注册，测试在类声明之前 `new` 它会报类不存在。每页条数 20/50/100 的限制放在控制器；被单测用来证明「先排序再分页」的服务不要把 `page_size=1` 改回 20。

测试站首次安装不要只跑 `thinkphp/base.php`。先初始化应用并载入 `vendor/thinkcmf/cmf/src/common.php`，否则没有 `cmf_parse_name()`。插件行用 `Db::name('plugin')->insertGetId()`，字段对照一条已安装的 addon（`type=1`、`module=addons`、`status=1`）。不要 `new PluginModel()` 去查或插，CLI 下它会找 `shd_plugin_model`。`install()` 成功后再插入注册行。菜单仍由插件目录里的 `menu.php` 在运行时读出，不必另行插菜单表。Hook 从本地调用点核对名称和事务时机；动账单、余额或外部通知时要有幂等键。前台身份只用 `request()->uid`，不信任请求里的 `uid`。写入校验权限、POST、字段白名单和输出转义。不记录密钥或完整令牌。插件内 Composer 要声明 PHP 7.2；不要在仓库根执行 `composer install` 或 `npm install`。`addons/export_excel` 的部分依赖要 PHP 7.4，不要用 PHP 7.2 去检查它的 `vendor/`。

## 验证与部署

本地：不含 vendor 的 `php -l`、有测试则跑不碰数据库的入口、模板脚本 `node --check`。失败先修。

只有用户明确要求，或已接受的变更阶段写明要部署时，才写入测试站。一次只同步一个插件目录。先 `rsync -rltni --checksum --safe-links` dry-run，再在 Web 根外备份，再：

```bash
stage_dir=$(mktemp -d /tmp/zjmf-addon-deploy.XXXXXX)
chmod 755 "$stage_dir"
rsync -rlt --safe-links --exclude='.git/' "$source_plugin_dir/" "$stage_dir/"
chown -R www:www "$stage_dir"
runuser -u www -- rsync -rlti --checksum --safe-links --exclude='.git/' \
  "$stage_dir/" "$target_dir/"
```

目标是 `/www/wwwroot/idc-test-dir/idc-test/public/plugins/<类型>/<插件名>/`。`idc-test-online-dir` 是放在 `/root` 下的软链，`www` 无法进入。`runuser -u www` 的 rsync 目标用上面的真实路径，暂存目录用 `/tmp`。禁止 `--delete`、`rsync -a`、整类目录同步。源目录里删除了文件时，rsync 不会去掉测试站上的旧文件；部署后用 `www` 身份只 `rm` 那一个目标路径。部署后属主为 `www:www`。新插件还要完成上一节的注册和建表，只同步文件时后台没有菜单，接口也没有表。

测试站版本写在其 `version` 文件里，可以高于解码仓库的 3.5.8，核心可能是 ionCube。插件契约仍以解码版 3.5.8 为准，不改测试站 `app/`。向上游拉目录时调用运行中的 `zjmfCurl`，不要按解码版缺失的分支在插件外补登录。页面测试用 `http://127.0.0.1` 加该站 `Host`，并带已有 `PHPSESSID`。沙箱访问不了本机时再申请权限，不要改用编辑器浏览器。

页面测试用已有后台会话，不索取密码。会话文件在 `/tmp/session/sess_*`，有效后台会话里能找到 `ADMIN_ID`。插件页未登录时 HTTP 仍是 200，正文 `status` 为 405、消息是「您还没有登录」，并下发新的 `PHPSESSID`。不要用编辑器浏览器直接打开 `/addons?_plugin=`，除非当前标签已经带着那个有效会话；否则这次导航会把已登录标签打回登录页。不执行未授权的刷新确认、重置确认或业务同步。门槛拒绝、取消确认可以测；会清零真实流量或解除暂停的确认，没有单独授权就不点。

Git：插件提交用 `git -C fan-zjmf-manger-decoded`，说明用中文。工作区的 `script/`、`docs/`、`openspec/` 用祖先仓库 `/root/devcode/fan-code-dir` 提交。只在用户要求时提交或推送。
