# Markdown 与飞书文档同步设计

## 概述

本设计定义了一条单一、手动触发的 V2 工作流，用于将 Git 仓库中的一篇 Markdown 文档与其绑定的一篇飞书文档保持同步。Git 中的 Markdown 是唯一真相源，飞书文档承担阅读、评论和协作讨论的角色。

这条工作流默认采取保守策略：

- 一次 sync 只处理一篇明确指定的 Markdown 文件。
- sync 必须由用户手动触发。
- sync 以 Git 基线、本地 Markdown 正文、飞书最新正文为输入进行三方合并。
- 飞书中所有未解决评论线程会被转成第二轮审稿 patch，作用于合并后的候选正文。
- 任何低置信度合并、无法判定的评论冲突或一致性校验失败，都会中止整次 sync。
- 成功收尾必须原子地完成以下动作：更新飞书正文、回读验证、解决全部未解决评论、回写本地 Markdown、创建专用 sync commit。

MVP 只支持纯文本 Markdown 与 fenced `mermaid` 代码块，不支持飞书画板、截图、图片、附件或其他不可稳定 round-trip 的非文本内容。

## 目标

- 让 Git 中的 Markdown 与绑定的飞书文档正文保持一致。
- 坚持 Markdown 是唯一持久化真相源。
- 允许协作者继续在飞书中通过评论进行讨论，而不是把主体编辑迁移到飞书。
- 使用 Git 历史承载 durable sync state，而不是提交运行态状态文件。
- 通过专用 sync commit 提供可审计的同步历史。

## 非目标

- 自动后台同步。
- 一次运行批量同步多篇 Markdown 文档。
- 全量支持飞书画板、图片、附件、截图或其他嵌入资源。
- 自动完成首次建链。
- 部分成功。该工作流是严格的 all-or-nothing。

## 支持范围

MVP 支持：

- 纯 Markdown 文本。
- 标题、列表、表格、引用、代码块等常规 Markdown 结构。
- fenced `mermaid` 代码块。

MVP 不支持：

- 飞书画板。
- 图片。
- 文件附件。
- 截图。
- 其他无法稳定 round-trip 的非文本块。

由此带来的设计约束：

- 所有代码围栏内容都应尽量逐字保留。
- `mermaid` 代码块属于高敏感文本块。
- 如果 `base -> local` 与 `base -> remote` 同时修改了同一个 `mermaid` 代码块，则直接判定为高风险并中止整次 sync。

## 真相源与状态模型

### 真相源

- 仓库中的 Markdown 是唯一真相源。
- 飞书正文是协作输入与合并输入，不是最终裁决源。

### Durable State

durable sync state 只存在于 Git 历史中，由每次成功 sync 生成的专用 commit 承载。

不创建受 Git 跟踪的 sidecar state 文件。

### 稳定配置

每篇 Markdown 文件在 frontmatter 中声明稳定绑定信息。

示例：

```yaml
---
title: 示例文档
markdown_larkdoc_sync:
  doc: https://example.feishu.cn/wiki/AbCdEfGh
  as: user
  profile: default
---
```

规则：

- frontmatter 只允许存放稳定绑定字段。
- `last_synced_commit`、cursor、hash 等运行态字段不得进入 frontmatter。
- diff、merge 和 consistency check 全部忽略 frontmatter。
- frontmatter 变更被视为绑定配置变化，而不是正文变化。

推荐字段：

- `doc`：必填。优先使用 URL，而不是原始 token。
- `as`：可选。`user` 或 `bot`，默认 `user`。
- `profile`：可选。为后续同步策略预留，MVP 使用 `default`。

### 本地运行 Journal

单次运行的恢复信息存放在 `.git` 目录下，不进入工作树。

建议路径：

- `.git/markdown-larkdoc-sync/runs/<run-id>.json`
- `.git/markdown-larkdoc-sync/artifacts/<run-id>/...`

这类 journal 只服务单次运行恢复与诊断，不受 Git 跟踪。

建议记录内容：

- 当前 phase
- 目标 Markdown 路径
- 解析后的 frontmatter
- 当前 doc_key
- 推导出的 last sync commit
- 当前抓取的 remote 正文
- 当前抓取的未解决评论线程
- merge report
- comment application report
- update plan
- 已执行的 API 步骤

## 飞书对象身份模型

frontmatter 中的 `doc` 应面向用户、以 URL 形式呈现。

工作流内部会把绑定的飞书对象解析成一个规范化身份：

```text
doc_key = <resolved_file_type>:<resolved_doc_token>
```

说明：

- 这里的 `token` 是飞书资源的内部对象 ID。
- `wiki` URL 中的 token 不一定等于底层真正操作的文档 token。
- 用户不应被要求直接管理 token。
- resolved token 主要用于执行和审计，不是主要配置入口。

## Sync Commit 约定

每次成功 sync 必须以一条专用 sync commit 结束。

建议的 commit message 形态：

```text
sync(markdown-larkdoc): docs/architecture.md

Markdown-Larkdoc-Sync: success
Markdown-Path: docs/architecture.md
Lark-Doc: https://example.feishu.cn/wiki/AbCdEfGh
Lark-Identity: user
Lark-Resolved-Doc-Token: doccnxxxxxxxx
Lark-Resolved-File-Type: docx
Lark-Sync-Profile: default
```

规则：

- 这条 commit 本身就是 durable sync record。
- 工作流不得把 `last_synced_commit` 写回任何文件。
- 下一次运行时，通过查询 Git 历史中的最近匹配 sync commit 来反推出基线。
- `Lark-Resolved-Doc-Token` 与 `Lark-Resolved-File-Type` 属于审计字段，用于重建 `doc_key`。

## 单次 Sync 工作流

一次 sync 只处理一篇 Markdown 文件。

### 第 1 步：Preflight

- 接收一个 Markdown 文件路径。
- 解析 frontmatter，提取稳定绑定字段。
- 校验目标文件已受 Git 跟踪。
- 校验仓库当前不处于未解决 merge 状态。
- 校验目标文件中不存在 conflict marker。
- 解析当前绑定文档，得到 `doc_key`。
- 根据 `doc_key` 查找最近一次成功的 sync commit。
- 如果不存在历史 sync commit，则中止并输出 bootstrap 建议。

### 第 2 步：载入 Base、Local、Remote

- `base_body`：通过 `git show <last_synced_commit>:<recorded_markdown_path>` 获取上次同步基线正文。
- `local_body`：当前工作区中的 Markdown 正文。
- `remote_body`：通过 `lark-cli docs +fetch` 获取飞书最新正文，并规范化。
- `open_comments`：获取飞书中当前所有未解决评论线程。

### 第 3 步：正文三方合并

合并对象只包含正文，不包含 frontmatter。

输入：

- `base_body`
- `local_body`
- `remote_body`

规则：

- 真正要合并的是 `base -> local` 与 `base -> remote` 两条变更。
- frontmatter 完全忽略。
- 只在代码块外做轻量格式归一化，例如空白、尾随空行和部分列表缩进噪音。
- 代码围栏内容逐字保留。
- `mermaid` 代码块按高敏感文本块处理。

直接中止的条件：

- 同一片正文区域被双方同时修改，且意图无法高置信判定。
- 一方删除、另一方深改。
- 标题结构被重排，导致稳定锚点失效。
- 同一个 `mermaid` 代码块被双方同时修改。

输出：

- `body_candidate`
- `merge_report.json`
- 每个 hunk 的 `confidence` 与 `reason`

### 第 4 步：评论转 Patch

把所有未解决评论线程转成第二轮 review pass，而不是简单追加文本。

每个评论线程应尽量被整理为结构化 review item，包含以下字段中的可恢复部分：

- anchor
- quoted text
- author
- thread id
- reply summary
- request type

规则：

- 仅落地评论所隐含的最小必要正文修改。
- 仅讨论性、提问性评论不强制改正文，但仍保留在最终报告中。
- 无法明确指向正文动作的评论，不自动改正文。

直接中止的条件：

- 评论锚点无法在 `body_candidate` 中重新定位，且无法高置信重定位。
- 多条评论之间存在实质冲突。
- 评论要求与更近的本地显式修改冲突，且无法判断优先级。
- 仍存在高风险的 `unapplied_comments`。

输出：

- `final_candidate`
- `comment_report.json`
- `unapplied_comments[]`

### 第 5 步：由 Sub-Agent 执行一致性审校

一致性校验必须交给独立 sub-agent 执行。

规则：

- sub-agent 使用与父 agent 相同的模型家族与推理配置。
- sub-agent 只读，不直接编辑文件。
- sub-agent 对完整的 `final_candidate` 进行审校，至少检查：
  - 标题层级一致性
  - 编号与引用连续性
  - 术语一致性
  - 跨章节逻辑矛盾
  - 删除后残留引用
  - 代码围栏闭合
  - ` ```mermaid` 围栏是否保留

父 agent 的行为约束：

- 父 agent 汇总 sub-agent findings。
- 只要存在高风险或低置信 finding，就中止整次 sync。
- 如果父 agent 根据 findings 又做了修正，则必须重新触发一次一致性审校，才能进入写回阶段。

### 第 6 步：Remote Write-Back Planning

默认禁止整体覆盖飞书文档。

必须先把 `remote_body -> final_candidate` 编译成一组最小更新步骤，使用 `lark-cli docs +update` 完成回写。

优先策略顺序：

1. `replace_range --selection-by-title`
2. `replace_range --selection-with-ellipsis`
3. `insert_before`
4. `insert_after`
5. `delete_range`

规则：

- 默认避免 `overwrite`。
- 除非用户显式允许，且文档可证明为安全的纯文本文档，否则 MVP 中禁止退化为 `overwrite`。
- 应优先选择最小且稳定的更新范围。

### 第 7 步：Remote 漂移检查与回写

在真正执行写回前，先再次抓取一遍 remote 正文。

规则：

- 如果 remote 在计划生成后已变化，则中止整次 sync，并要求重新执行。
- 按计划执行 `docs +update`。
- 写回后再次 `fetch`。
- 重新规范化后，验证飞书正文是否与 `final_candidate` 一致。

如果验证失败：

- 中止整次 sync
- 不 resolve 评论
- 不创建 sync commit

### 第 8 步：本地收尾与原子闭环

只有在 remote 验证通过之后，才能进入收尾：

- 将 `final_candidate` 回写到本地 Markdown 正文，保留原 frontmatter。
- 拉取该文档当前所有未解决评论。
- 将这些未解决评论全部 resolve。
- 创建专用 sync commit。

成功收尾的定义：

- 飞书正文与 `final_candidate` 一致。
- 当前全部未解决评论均已解决。
- 专用 sync commit 已创建。

## 失败策略

从是否形成成功 sync record 的角度看，该工作流是严格 all-or-nothing。

出现以下任一情况时，中止且不创建 sync commit：

- 不存在历史同步基线。
- 绑定存在歧义或检测到 rebind 冲突。
- 三方合并低置信。
- 存在高风险且未应用的评论。
- 一致性审校失败。
- 写回前 remote 漂移。
- 写回后 remote 验证失败。
- 评论解决失败。
- sync commit 创建失败。

如果 remote 写回成功，但本地回写或 commit 失败，该次运行仍视为失败，并必须给出明确的恢复建议。

## 基线发现规则

### 规范化身份

基线归属对象是 `doc_key`，不是当前文件路径，也不是 frontmatter 中原始填写的 URL 字符串。

### 查找 Last Sync Commit

规则：

1. 解析 frontmatter。
2. 解析当前 `doc_key`。
3. 在 Git 历史中查找成功的 sync commit。
4. 仅接受 `Lark-Resolved-File-Type` 与 `Lark-Resolved-Doc-Token` 同时匹配当前 `doc_key` 的 commit。
5. 使用该 commit 中记录的 `Markdown-Path` 来读取基线文件。

禁止 path-only fallback。

### Rename 处理

如果 `doc_key` 匹配，但历史 commit 记录的 `Markdown-Path` 与当前路径不同，则将其视为 rename 候选，而不是立即报错。

规则：

- 基线仍从旧路径读取。
- 本次 sync 成功后，在新的 sync commit 中记录当前路径。
- 如果旧路径在当前 `HEAD` 中仍存在，并且看起来仍是一条活跃文档线，则中止并提示绑定歧义。

### Rebind 处理

如果当前路径曾经有 sync 历史，但当前 `doc_key` 与历史成功 sync commit 中记录的文档身份不同，则视为 rebind 尝试。

规则：

- 不继承旧基线。
- 不跨文档做三方合并。
- 直接中止，并要求用户显式处理。

### 首次建链

如果当前 `doc_key` 在 Git 历史中完全找不到成功 sync commit，则视为首次建链。

MVP 中不自动建链，而是返回 bootstrap 建议，至少包括：

- local 与 remote 正文是否看起来一致。
- 当前是否存在未解决评论。
- 用户应先人工对齐 Markdown 到飞书，还是先对齐飞书到 Markdown，再重新触发 sync。

## 脚本层

涉及结构化解析的 Git/Lark 操作应优先实现为脚本，而不是只放在 prompt 约束中。

### 必需脚本

#### `scripts/resolve_doc_key.py`

输入：

- Markdown 路径，或 frontmatter 中声明的 doc 引用

输出 JSON：

- `declared_doc`
- `resolved_doc_token`
- `resolved_file_type`
- `doc_key`

#### `scripts/find_last_sync_commit.py`

输入：

- Markdown 路径
- `doc_key`

输出 JSON：

- `status`: `found | not_found | conflict`
- `doc_key`
- `commit`
- `markdown_path`
- `reason`

规则：

- `conflict` 用于表达候选冲突、rebind 检测和 rename 冲突。
- agent 不得自己手写 `git log` 解析逻辑，必须统一调用该脚本。

#### `scripts/extract_markdown_body.py`

输入：

- Markdown 文件路径或 stdin

输出 JSON：

- `frontmatter`
- `body`

### 推荐补充脚本

- `scripts/fetch_open_comments.py`
- `scripts/resolve_all_comments.py`
- `scripts/create_sync_commit.py`

这些脚本都应输出稳定 JSON，便于 agent 消费。

## Agent 职责分工

### 父 Agent

父 agent 是整个工作流的 orchestrator。

职责：

- 调用确定性脚本
- 载入 base/local/remote 正文
- 执行正文三方合并
- 将评论转成 review patch
- 生成 update plan
- 执行飞书写回
- 回写本地 Markdown
- 解决评论
- 创建 sync commit

### Sub-Agent

MVP 中只保留一个 sub-agent。

职责：

- 在第 5 步执行只读一致性审校
- 使用与父 agent 相同的模型家族和推理配置
- 仅返回 findings，不直接改文件

sub-agent 不负责执行主工作流，也不直接落地变更。

## 用户触发接口

skill 对外只暴露一个手动触发的 V2 工作流。

典型触发表达：

- 同步 `docs/architecture.md` 与它绑定的飞书文档
- 对 `docs/architecture.md` 执行一次 sync，目标文档取自 frontmatter

每次运行都必须显式指定一篇 Markdown 路径。

## Git 工作区规则

- 允许仓库中存在与本次 sync 无关的其他改动。
- sync commit 只应 stage 并提交目标 Markdown 文件。
- 如果仓库正处于未解决 merge 状态，则直接中止。
- 如果目标 Markdown 文件存在 conflict marker，则直接中止。
- 如果 remote 写回成功，但本地 commit 失败，则必须输出恢复建议，且不得将这次运行标记为成功。

## 可观测性与产物

每次运行都应留下足够的 machine-readable 产物，便于调试与诊断。

建议产物：

- `merge_report.json`
- `comment_report.json`
- 规划出的飞书 update operations
- 最终 validation summary
- comment resolve 结果

这些产物都应放在本地 `.git/markdown-larkdoc-sync/...` 运行目录中。

## 已知风险

- 飞书评论 patch 接口虽然在参考仓库中有文档线索，但其真实请求结构仍需要在实际运行环境中验证。
- 大规模标题重排会降低 `selection-by-title` 更新规划的稳定性。
- 即使本地遵循原子闭环语义，remote 写回后的网络故障仍可能要求用户进行一次带指引的修复流程。

## 建议

MVP 应围绕本文描述的保守型单文档 V2 工作流实现。

实现优先级建议：

1. 先把 frontmatter、Git 历史和 doc_key 解析做成脚本。
2. 三方合并和评论落地保持保守策略。
3. 把 sub-agent 一致性审校做成必经步骤。
4. 在任何低置信场景下优先中止，而不是冒险自动修改。
5. 把审计能力收敛到专用 sync commit，而不是状态文件。

## 最终验证命令集合（Task 8 收口）

- `python3 -m pytest tests/test_cli_smoke_contracts.py -q`
- `python3 -m pytest tests/test_markdown_body.py tests/test_doc_binding.py tests/test_git_sync.py tests/test_comments.py -q`
- `python3 -m pytest`
