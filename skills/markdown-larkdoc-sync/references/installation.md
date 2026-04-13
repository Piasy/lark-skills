# 安装与前置说明

## 安装命令

- 全量安装：`npx skills add Piasy/lark-skills -g -y`
- 单 skill 安装：`npx skills add Piasy/lark-skills -s markdown-larkdoc-sync -g -y`
- 本地安装：`npx skills add . -g -y`

## 运行前提

- `python3 >= 3.11`
- `git`
- `lark-cli`
- 已完成 `lark-cli` 认证

## profile 约定

- 本 skill 的 `profile` 指 lark-cli profile（通常等于 appId）。
- 不要默认使用字符串 `default`，先用 `lark-cli auth list` / `lark-cli config show` 确认可用 profile。
- `create_bootstrap_doc.py` 可不传 `--profile`，脚本会优先使用 active profile，其次在仅有一个 profile 时自动选择。
