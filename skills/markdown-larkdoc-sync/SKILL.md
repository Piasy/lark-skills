---
name: markdown-larkdoc-sync
description: Use when需要对一篇 Markdown 与其绑定飞书文档执行手动同步，并要求遵循 Git 基线、评论读取与解决、sub-agent 一致性审校和专用 sync commit 收尾。
---

# markdown-larkdoc-sync

开始前先确认：

- 只支持一个手动触发的同步工作流。
- 每次只处理一篇明确指定的 Markdown 文件。
- frontmatter 是受限子集，绑定读写必须走脚本。
- 一致性审校必须由独立 sub-agent 执行，且 sub-agent 使用与父 agent 相同的模型配置。
- 成功收尾时要解决全部未解决评论，并创建专用 sync commit。
- Mermaid 特殊约束：飞书正文中必须落地为“文本绘图 add-on（codeChart）”，不能保留 whiteboard 块。

执行约束：

- 确定性结构化步骤优先调用仓库脚本，不要在 prompt 中手写 Git 或 Lark 解析逻辑。
- `bin/resolve_doc_key.py`、`bin/find_last_sync_commit.py`、`bin/extract_markdown_body.py`、`bin/fetch_open_comments.py`、`bin/fetch_remote_markdown.py`、`bin/write_back_and_verify.py`、`bin/resolve_all_comments.py`、`bin/create_sync_commit.py`、`bin/create_bootstrap_doc.py` 都应被视为工作流标准入口。
- 调用 `bin/find_last_sync_commit.py` 时，第二个参数 `doc_key` 必须直接使用 `bin/resolve_doc_key.py` 输出中的 `doc_key` 原值。
- `doc_key` 格式固定为 `<file_type>:<resolved_doc_token>`（示例：`docx:KlpudvT7so6kfwxyzZsl0L9ogbg`），不得手工改写成 `docx/KlpudvT7so6kfwxyzZsl0L9ogbg` 这类 `/` 分隔格式。
- `profile` 必须使用本机可用的 lark-cli profile（通常为 appId），不要硬编码 `default`。可用值通过 `lark-cli auth list` 和 `lark-cli config show` 确认。
- 调用 `bin/create_bootstrap_doc.py` 时可以不传 `--profile` 让脚本自动选择；若传入的 `--profile` 不可用，脚本会按 active profile 或单 profile 自动回退，并在输出中标记 `profile_resolution` / `profile_warning`。
- 读取 frontmatter 绑定必须调用 `bin/read_frontmatter_binding.py`。
- 修改 frontmatter 绑定必须调用 `bin/write_frontmatter_binding.py`。
- 读取远端正文用于合并或落盘时，必须调用 `bin/fetch_remote_markdown.py --canonical`，禁止直接使用 `docs +fetch` 原始文本参与比较。
- 回写飞书必须调用 `bin/write_back_and_verify.py`，并使用脚本内置的 `overwrite` 策略。
- `bin/write_back_and_verify.py` 会先写占位符，再通过 raw docx block API 把 mermaid 占位符替换为文本绘图 add-on（`block_type=40`，`view=codeChart`）。
- 当本地包含 mermaid 代码块时，若回读仍出现 `<whiteboard .../>`，视为写回验证失败并中止 sync。
- agent 不得手改 frontmatter。
- agent 不得自行解析 frontmatter。
- sync commit message 与 `Markdown-Path` trailer 中的 `markdown_path` 必须是相对于 git repo root 的相对路径，不得写入绝对路径或基于当前目录的非归一化路径。
- 任何低置信合并、评论冲突、一致性审校失败、remote 漂移或写回验证失败，都要中止整次 sync。

执行顺序：

1. 调用 `bin/read_frontmatter_binding.py` 读取绑定与正文。
2. 调用 `bin/resolve_doc_key.py`。
3. 调用 `bin/find_last_sync_commit.py`，并直接复用上一步产出的 `doc_key` 参数。
4. 调用 `bin/fetch_remote_markdown.py --canonical` 获取远端正文，并调用 `bin/fetch_open_comments.py` 获取当前全部未解决评论。
5. 做正文三方合并。
6. 把评论转成 review patch。
7. 调用 sub-agent 做一致性审校。
8. 调用 `bin/write_back_and_verify.py` 回写飞书并验证（含 mermaid->文本绘图 add-on 替换和 canonical 回读比对）。
9. 调用 `bin/resolve_all_comments.py`，解决当前文档全部未解决评论。
10. 调用 `bin/create_sync_commit.py`。

首版建链（本地已有 Markdown，远端还没有文档）必须流程：

1. 调用 `bin/create_bootstrap_doc.py <markdown_path> --title <title> --identity <user|bot> [--profile <appId>]` 创建初版飞书文档，并在脚本输出中确认 `auto_normalized=true` 且 `normalized_verified=true`。
2. 从输出中获取 `doc_id` / `doc_url`，并调用 `bin/write_frontmatter_binding.py` 写回 frontmatter 绑定；`--profile` 必须使用输出中的 `effective_profile`（不要继续写入无效 profile）。
3. 若 `create_bootstrap_doc.py` 返回非零或 `normalized_verified=false`，必须中止本次 sync，不得进入收尾步骤。
4. 完成后按常规流程进入 `bin/create_sync_commit.py` 收尾。

收尾成功条件：

- 飞书 canonical 正文与最终候选正文一致。
- Mermaid 代码块在飞书中已落地为文本绘图 add-on（codeChart）。
- 当前文档全部未解决评论均已解决。
- 已创建专用 sync commit。

参考文档：

- frontmatter 受限子集：`references/frontmatter-subset.md`
- 安装与前置说明：`references/installation.md`
