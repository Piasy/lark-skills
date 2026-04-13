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

- `markdown-larkdoc-sync`：用于手动同步单篇 Markdown 与飞书文档，提供 frontmatter 绑定读取/写回、文档 key 解析、同步基线查询、评论拉取与批量解决、sync commit 收尾等脚本化流程。

当前仓库仅包含上述一个 skill；后续以 `skills/` 目录中可扫描到的 `SKILL.md` 为准。

## 触发 Prompt 示例

调用该流程时，请在 prompt 中显式写出 skill 名称 `markdown-larkdoc-sync`。
这样可以避免误触发其他也会调用 `lark-cli` 的 `lark-*` skill。

示例 prompt：

```text
请使用 markdown-larkdoc-sync skill，把 docs/weekly.md 同步到它绑定的飞书文档。
```

## License

本仓库使用 MIT License。
