# Frontmatter 受限子集

本 skill 的 frontmatter 不是通用 YAML，而是受限子集。

## 顶层键白名单

- `title`
- `markdown_larkdoc_sync`

## 子键白名单

`markdown_larkdoc_sync` 仅允许：

- `doc`
- `as`
- `profile`

## 字段约束

- `as` 仅允许 `user`、`bot`
- 不支持 list
- 不支持 anchor / alias
- 不支持 tag
- 不支持多行 block scalar

## 读写约束

- 读取绑定必须调用 `bin/read_frontmatter_binding.py`
- 修改绑定必须调用 `bin/write_frontmatter_binding.py`
- agent 不得手改 frontmatter
- agent 不得自行解析 frontmatter
