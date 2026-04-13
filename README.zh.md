# lark-skills（中文说明）

这是一个可直接被 `npx skills add` 消费的 skills source repository。

## 仓库定位

- 仓库名：`Piasy/lark-skills`
- 目标：让用户通过 skills CLI 直接安装并使用 skill
- 安装时不需要先手动 clone 仓库

## 核心 Skill 工作流（重点）

### `markdown-larkdoc-sync`：从文档产出到评审闭环

`markdown-larkdoc-sync` 不只是“同步一下文档”，而是一个脚本优先、可审计的单文档同步流程。  
它重点解决的是团队协作中的评审回流问题：

1. 第一次运行 skill：从本地 Markdown 创建/初始化 Lark Doc。
2. 同事在 Lark Doc 中直接 review 并发表评论。
3. 评审后第二次运行 skill：拉取未解决评论和远端 canonical Markdown。
4. 把评审意见回流到本地 Markdown 并更新内容。
5. 回写 Lark Doc、校验一致性、批量解决评论，并创建专用 sync commit。

最终效果是：评审发生在飞书，事实来源保持在 Markdown，变化轨迹沉淀在 Git。

说明：这里的“自动”是指在 agent 明确触发后由脚本执行，不是后台持续自动同步。

## 流程图约束

- Markdown 中的流程图使用 Mermaid 代码块。
- 飞书文档中的对应图形落地为文本绘图 add-on（`codeChart`）。
- 该流程不会把这类图写成画板（whiteboard）块。

## 该工作流脚本化覆盖范围

- frontmatter 绑定读取/写回脚本化（禁止手改、禁止手写解析）
- 文档 key 解析与 Git 同步基线定位
- 远端 canonical Markdown 拉取与合并保障
- 评论拉取与批量解决
- `overwrite` 回写校验与 Mermaid 到 `codeChart` 的转换处理
- 专用 sync commit 收尾，保证可追溯

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

## License

本仓库使用 MIT License。
