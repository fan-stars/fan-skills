# 打包给其他项目

本工作流由两个自研 skill 组成，**一起拷贝**即可，无需附带业务侧的 `site-rewrite/`。

## 拷贝内容

```
f-site-rewrite-init/
  SKILL.md
  scaffold/                 # 唯一骨架真相源
  config.template.yaml
  secrets.example.env
  indexes.md
  data-api-record-template.md
  PACKAGING.md

f-site-rewrite-implement/
  SKILL.md
  match-rubric.md
  observation-template.md
```

放到目标仓库例如：

- `.agents/skills/`（与本仓一致）
- 或 Cursor 项目 skills 约定目录

## 首次使用

1. 在目标项目打开对话，运行 `/f-site-rewrite-init`  
2. Agent 将 `f-site-rewrite-init/scaffold/` **复制**为项目根 `site-rewrite/`  
3. 填写配置与 `secrets.local.env`  
4. 再跑 `/f-site-rewrite-implement`

## 注意

- `scaffold/` 内不得含真实密钥或客户域名  
- 项目根 `site-rewrite/secrets.local.env` 必须 gitignore  
- 升级 skill 时：用 `cp -an scaffold/. site-rewrite/` 只补缺失文件，勿覆盖用户配置与 secrets  
