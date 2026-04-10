---
name: markdown-larkdoc-sync
description: 单篇 Markdown 与绑定飞书文档的手动 V2 同步工作流。适用于正文三方合并、评论读取与解决、Git 基线发现和专用 sync commit 收尾。
---

# markdown-larkdoc-sync

开始前先确认：

- 只支持一个手动触发的 V2 工作流。
- 每次只处理一篇明确指定的 Markdown 文件。
- frontmatter 只读取稳定绑定字段。
- 一致性审校必须由独立 sub-agent 执行，且 sub-agent 使用与父 agent 相同的模型配置。
- 成功收尾时要解决全部未解决评论，并创建专用 sync commit。

执行顺序：

1. 调用 `scripts/extract_markdown_body.py`
2. 调用 `scripts/resolve_doc_key.py`
3. 调用 `scripts/find_last_sync_commit.py`
4. 读取远端正文与未解决评论
5. 做正文三方合并
6. 把评论转成 review patch
7. 调用 sub-agent 做一致性审校
8. 回写飞书并验证
9. 解决全部未解决评论
10. 调用 `scripts/create_sync_commit.py`
