# 字段判断

`codegen_update` 之前按本节顺序做十二次判断。每一次把对应标题下的全文交给模型，不靠上一轮记忆。

## 注释

输入按这个顺序拼：

1. 本表完整的 `CREATE TABLE`
2. 关联表完整的 `CREATE TABLE`。列名以 `_id` 结尾时，去掉后缀，在本次 DDL 和已导入表里找表名等于该词、等于「模块名_该词」或等于「当前表前缀_该词」的表。`member.level_id` 附带 `member_level`。指向本表的自关联只写「自关联」，不重复粘贴本表。列注释里的 `某表.某列` 或反引号表名也附上。找不到就写「无关联表」，不编造 DDL
3. 本步问题：为每一列写短 `columnComment`，并写删掉了什么。上限 8 个汉字，能用 2 到 4 个字就用短的。括号枚举、预留、加密、不 DROP、存储说明都不留。表注释是长句时，另给一个短 `classComment`

按 `codegen_detail` 的列顺序一列一行，列名都要出现。漏列或「其余不要」就重做。`columnComment` 同时是列表标题、搜索标签、表单标签和 Java 注释。

## 字典

输入与「注释」相同，再附本地已有 `system_dict_type` / `system_dict_data`（类型、值、文案），以及技能说明里的枚举格式示例。

每一列只能是 **绑定** / **新建** / **不绑定**。绑定：取值和文案与某个已有字典全部一致。还能绑定的已有字典，类型名只允许 `common_` 或当前模块名加下划线。语义是「是否」的列绑定 `common_status`（`0` 开启，`1` 关闭），`codegen_update` 把该列 `javaType` 写成 `Integer`。不绑定其他模块前缀的字典。新建的类型名以 `{moduleName}_` 开头，不新建 `common_`。新建：注释已有值与中文文案、且没有完全相同的已有字典；类型名模块名加下划线；每个取值给 `value` / 中文 `label` / 大写 `constant`。不绑定：其余情况 `dictType` 为空。没有成对中文文案则不新建。

不要按列名指定该绑哪个字典。一列一行，列名都要出现。

结论写入 `.tmp/dict-decision.json`（不提交），形状含 `columns[].action`（`bind`|`create`|`none`）与 `creates[]`（仅 create）：

```text
{
  "columns": [
    {"column": "status", "action": "bind", "dictType": "common_status"},
    {"column": "flag", "action": "create", "dictType": "demo_flag"},
    {"column": "token", "action": "none"}
  ],
  "creates": [
    {
      "dictType": "demo_flag",
      "values": [
        {"value": "0", "label": "开启", "constant": "ENABLE"},
        {"value": "1", "label": "关闭", "constant": "DISABLE"}
      ]
    }
  ]
}
```

示例里的 `common_status` / `demo_flag` 只演示 JSON 字段，不是「某列必须绑谁」的规则。

漏列、「其余不要」、同一列又绑定又新建、常量名不是 `^[A-Z][A-Z0-9_]*$`，都重做。

## 查询

输入与「注释」相同。

为每一列回答 `listOperation`：进不进筛选。一列一行，列名都要出现。密码类列（列名或注释命中密码、操作密码、密钥哈希、私钥）固定为否。

## 查询方式

输入与「注释」相同。

为每一列回答 `listOperationCondition`。只用 `=`、`!=`、`>`、`>=`、`<`、`<=`、`LIKE`、`BETWEEN`。进筛选的列优先 `=`、`LIKE`、`BETWEEN`；用其他运算符时写一句理由。时间筛选用 `BETWEEN`。不进筛选的列仍写一行，条件可写 `-`。一列一行，列名都要出现。

## 显示类型

输入与「注释」相同。

为每一列回答 `htmlType`。只用 `input`、`textarea`、`select`、`radio`、`checkbox`、`datetime`、`imageUpload`、`fileUpload`、`editor`。时间筛选同时写 `htmlType=datetime`。有非空 `dictType` 的列用 `select`（或 `radio`）。语义是「是否」且已绑定 `common_status` 的列用 `radio`。`select` 或 `radio` 只在该列字典结论有非空 `dictType` 时使用。没有字典却选了这两类，停止，不调用 `codegen_update`。一列一行，列名都要出现。

## 允许空

输入与「注释」相同。

为每一列回答 `nullable`：真或假。只写入代码生成元数据，驱动校验和表单必填。本步不发 `ALTER`，不改物理列的 `NULL` / `NOT NULL`。一列一行，列名都要出现。

## 列表

输入与「注释」相同。

为每一列回答 `listOperationResult`：展示或不展示。一列一行，列名都要出现。密码类列（列名或注释命中密码、操作密码、密钥哈希、私钥）固定为否。

## 插入

输入与「注释」相同。

为每一列回答 `createOperation`：要或不要。一列一行。页面模板会把新增或编辑任一为 true 的列放进同一张表单，本步仍只回答插入。密码类列（列名或注释命中密码、操作密码、密钥哈希、私钥）固定为否。

## 编辑

输入与「注释」相同。

为每一列回答 `updateOperation`：要或不要。可以与插入不同。一列一行。主键 `id` 这一格固定写 true。模板因主键排除它，编辑页不展示 `id`。密码类列（列名或注释命中密码、操作密码、密钥哈希、私钥）固定为否。

## 列宽

输入与「注释」相同，再附上本文件的「列宽定稿」全文。

只回答列表里展示的列：类别和 `colWidth` 像素。类别使用定稿表里的判定。数字用该行的整数。某一列明显更长或更短时可以改，并写一句理由。列表不展示的列不写宽度，更新时 `colWidth` 传 null。

本文件没有「列宽定稿」，或表里有空单元格、空类别、非整数时，停止。不调用 `codegen_update`，不用模板里的 120 填空。候选像素不写进本文件。

## 列宽定稿

| 类别 | 判定 | colWidth |
|---|---|---|
| 编号 | 主键 id、短整数编号 | 80 |
| 状态 | 状态、是否、短枚举展示 | 100 |
| 短名称 | 名称、昵称、手机号等约 2–10 字 | 120 |
| 中等文本 | 公司、短备注、等级名 | 150 |
| 时间 | 创建时间、更新时间、登录时间等 | 180 |
| 长文本 | 地址、长备注、邮箱、URL | 200 |

## 菜单

输入按这个顺序拼：

1. 本表完整的 `CREATE TABLE`
2. 关联表完整的 `CREATE TABLE`。规则与「注释」相同
3. 本地 SQL 里已有菜单。每行：编号、中文名、路径、图标、`parent_id`
4. 本步问题

回答四项：挂到哪个已有父菜单；没有合适父级时的新父菜单中文名；本页中文名；父菜单图标和本页图标。中文名是 2–6 个汉字。本页名不带「管理」。同一父级下用页面自己的名字区分，例如「会员用户」「会员分组」。

图标只能从下面的清单里选一个。清单外的名字停止，不调用 `codegen_update`。

`ep:avatar` `ep:chat-dot-round` `ep:collection` `ep:connection` `ep:document` `ep:document-copy` `ep:house` `ep:link` `ep:list` `ep:menu` `ep:message` `ep:message-box` `ep:position` `ep:promotion` `ep:set-up` `ep:takeaway-box` `ep:tools` `ep:user`

父菜单已经存在时仍要回答图标。落盘只复用它的编号，不改它的中文名和图标。路径、组件、权限不由本步改。

## 排序

输入与「注释」相同。

为每一列写 `ordinalPosition`：从 1 开始的连续整数，一列一行，列名都要出现。隐藏列也要有号。创建时间、更新时间默认排在业务列后面。改掉这个默认时写一句理由。

漏列、重复或断号就重做。不调用 `codegen_update`。
