---
name: markdown-larkdoc-sync
description: Use when需要对一篇 Markdown 与其绑定飞书文档执行手动同步，并要求遵循 Git 基线、评论读取与解决、sub-agent 一致性审校和专用 sync commit 收尾。
---

# markdown-larkdoc-sync

开始前先确认：

- 只支持一个手动触发的同步工作流。
- 每次只处理一篇明确指定的 Markdown 文件。
- frontmatter 只读取稳定绑定字段。
- 一致性审校必须由独立 sub-agent 执行，且 sub-agent 使用与父 agent 相同的模型配置。
- 成功收尾时要解决全部未解决评论，并创建专用 sync commit。

执行约束：

- 确定性结构化步骤优先调用仓库脚本，不要在 prompt 中手写 Git 或 Lark 解析逻辑。
- `scripts/resolve_doc_key.py`、`scripts/find_last_sync_commit.py`、`scripts/extract_markdown_body.py`、`scripts/fetch_open_comments.py`、`scripts/resolve_all_comments.py`、`scripts/create_sync_commit.py` 都应被视为工作流的标准入口。
- 任何低置信合并、评论冲突、一致性审校失败、remote 漂移或写回验证失败，都要中止整次 sync。

执行顺序：

1. 调用 `scripts/extract_markdown_body.py`
2. 调用 `scripts/resolve_doc_key.py`
3. 调用 `scripts/find_last_sync_commit.py`
4. 读取远端正文，并调用 `scripts/fetch_open_comments.py` 获取当前全部未解决评论
5. 做正文三方合并
6. 把评论转成 review patch
7. 调用 sub-agent 做一致性审校
8. 回写飞书并验证
9. 调用 `scripts/resolve_all_comments.py`，解决当前文档全部未解决评论
10. 调用 `scripts/create_sync_commit.py`

收尾成功条件：

- 飞书正文与最终候选正文一致。
- 当前文档全部未解决评论均已解决。
- 已创建专用 sync commit。
