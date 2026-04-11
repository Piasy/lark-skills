# lark-skills（中文说明）

这是一个可直接被 `npx skills add` 消费的 skills source repository。

## 仓库定位

- 仓库名：`Piasy/lark-skills`
- 目标：让用户通过 skills CLI 直接安装并使用 skill
- 安装时不需要先手动 clone 仓库

## 安装命令

- 全量安装：`npx skills add Piasy/lark-skills -g -y`
- 单 skill 安装：`npx skills add Piasy/lark-skills -s markdown-larkdoc-sync -g -y`
- 本地安装（开发调试）：`npx skills add . -g -y`
- 列出可安装 skill：`npx skills add Piasy/lark-skills -g -y --list`

## 工作方式

skills 工具会拉取 source repository 并扫描其中的 `SKILL.md`。运行时入口位于各 skill 目录内部。

## 运行前提

- `python3 >= 3.11`
- `git`
- `lark-cli`
- 已完成 `lark-cli` 认证

## frontmatter 约束

`markdown-larkdoc-sync` 的 frontmatter 是受限子集，不是通用 YAML。绑定读写必须走脚本入口，不能手改。

## 当前 skills

- `markdown-larkdoc-sync`

## License

本仓库使用 MIT License。
