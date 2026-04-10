# Task 5 Step 5 Schema 校验补充证据

## 背景

Task 5（评论读取与批量 resolve）的 Step 5 原要求执行：

- `lark-cli schema drive.file.comments.patch`

用于确认 `drive.file.comments.patch` 的请求体字段与 `build_resolve_payload()` 一致。

## 执行证据（受环境限制）

- 执行日期：2026-04-10（Asia/Shanghai）
- 执行目录：`/Users/linker/src/Piasy/markdown-larkdoc-sync`
- 执行命令：`lark-cli schema drive.file.comments.patch`
- 实际输出：`zsh:1: command not found: lark-cli`
- 结论：当前执行环境未提供 `lark-cli` 可执行程序，无法完成原始 schema introspection。

## 替代校验与可审计性

在无法直接执行 `lark-cli schema` 的前提下，新增并保留自动化字段契约测试，锁定 patch payload 的关键字段名，防止回归：

- 测试文件：`tests/test_comments.py`
- 用例：`test_build_resolve_payload_schema_field_contract`
- 契约断言：
  - `payload['params']` 仅包含 `file_token`
  - `payload['data']` 仅包含 `file_type` / `comment_id` / `is_solved`
- 既有值断言用例：`test_build_resolve_payload_marks_comment_solved`

该替代校验可在 CI 与本地持续执行，确保 Step 5 关注的 schema 关键字段不会被误改。

## 环境恢复后的补跑要求

当运行环境具备 `lark-cli` 后，需补跑：

- `lark-cli schema drive.file.comments.patch`

并将输出结果追加到本文件，完成对 Step 5 原始要求的闭环验证。
