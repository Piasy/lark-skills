# lark-skills 打包与运行时设计

## 概述

本设计定义 `Piasy/lark-skills` 作为一个可被 `npx skills add <repo>` 直接消费的多-skill 仓库的发布形态、运行时结构和安装约定。

当前仓库首个对外发布的 skill 为 `markdown-larkdoc-sync`。目标不是把现有仓库继续当作一个普通 Python 项目使用，而是把 `skills/markdown-larkdoc-sync/` 收敛成唯一运行时真相源，使其在远程安装后无需额外 clone 仓库、无需额外安装 Python 第三方依赖即可运行。

本设计同时收紧 frontmatter 语义：frontmatter 不再被视为通用 YAML，而是由脚本全权管理的受限子集格式。所有读取和修改绑定配置的行为都必须通过 skill 自带脚本完成。

## 背景与问题

当前仓库的脚本与公共模块位于仓库根 `scripts/` 和 `src/` 下，而 `npx skills add` 只会安装 skill 目录本身包含的文件。实际验证表明：

- 远程或本地通过 `npx skills add` 安装后，agent 目录里会拿到 `SKILL.md`、`agents/` 以及 skill 目录内的 `references/` 等内容。
- 仓库根 `scripts/` 与 `src/` 不会随安装一起进入 agent 可见目录。
- 因此如果 skill 文档引用仓库根脚本路径，远程安装后的用户无法实际执行这些脚本。

与此同时，现有 frontmatter 解析逻辑仍以 `PyYAML` 为主路径，并在无依赖环境下回退到简化解析器。这造成了三个问题：

- skill 安装本身不会自动安装 Python 运行时依赖。
- 用户只安装 skill 但没有 `PyYAML` 时，行为会从完整 YAML 解析静默退化为受限解析。
- frontmatter 的语义边界对用户和 agent 都不够清晰。

## 目标

- 仓库可直接通过 `npx skills add Piasy/lark-skills -g -y` 远程安装，无需用户手动 clone。
- 远程安装后的 `markdown-larkdoc-sync` skill 包含全部运行时资产，不依赖仓库根目录存在。
- Python 运行时不依赖 `PyYAML` 等第三方包。
- frontmatter 采用受限子集格式，读取与修改全部走脚本。
- `resolve_all_comments.py` 等脚本语义与设计工作流、skill 描述和脚本命名保持一致。
- README 明确说明安装方式、运行前提、技能范围和 frontmatter 约束。

## 非目标

- 不实现自定义跨 agent 安装器。
- 不维护 agent 目录映射或兼容矩阵，agent 适配继续以 `skills` 工具为唯一真相源。
- 不继续承诺 frontmatter 兼容任意合法 YAML。
- 不把本仓库包装成 npm 包或独立 Python 包。
- 不在本设计中补齐完整 sync 工作流尚未实现的三方合并、remote write-back planning 等大功能。

## 安装模型

### 对外安装命令

远程安装全部 skills：

```bash
npx skills add Piasy/lark-skills -g -y
```

只安装 `markdown-larkdoc-sync`：

```bash
npx skills add Piasy/lark-skills -s markdown-larkdoc-sync -g -y
```

本地开发安装：

```bash
npx skills add . -g -y
```

只列出可安装 skill，不执行安装：

```bash
npx skills add Piasy/lark-skills -g -y --list
```

### 工作原理

- 当 `source` 为 GitHub 仓库或 Git URL 时，`skills` 工具会自动下载仓库到临时目录，再扫描其中的 `SKILL.md`。
- 当 `source` 为本地路径时，`skills` 工具直接扫描本地目录。
- `skills` 工具会把 skill 目录内的文件安装到 agent 可见目录。
- 仓库根目录文件不会被视为 skill 运行时资产。

### 运行前提

用户环境只要求：

- `python3 >= 3.11`
- `git`
- `lark-cli`
- 已完成 `lark-cli` 认证与授权

不再要求额外安装 `PyYAML` 或其他 Python 第三方包。

## 仓库发布结构

发布后仓库的运行时真相源位于 `skills/` 目录中。推荐结构如下：

```text
README.md
README.zh.md
LICENSE
pyproject.toml
tests/
  markdown-larkdoc-sync/
docs/
skills/
  markdown-larkdoc-sync/
    SKILL.md
    agents/
      openai.yaml
    bin/
      extract_markdown_body.py
      read_frontmatter_binding.py
      write_frontmatter_binding.py
      resolve_doc_key.py
      find_last_sync_commit.py
      fetch_open_comments.py
      resolve_all_comments.py
      create_sync_commit.py
    lib/
      __init__.py
      jsonio.py
      frontmatter.py
      lark_cli.py
      doc_binding.py
      git_sync.py
      comments.py
      journal.py
    references/
      frontmatter-subset.md
      installation.md
```

约束如下：

- 删除仓库根 `scripts/` 与 `src/`，避免形成双真相源。
- `skills/markdown-larkdoc-sync/` 是唯一运行时真相源。
- 根 `tests/` 按 skill 子目录组织，`docs/` 与 `pyproject.toml` 仅服务开发与验证，不参与 skill 安装载荷。
- 根 `LICENSE` 使用 MIT。

## 运行时架构

### `bin/`

`bin/` 中的文件是用户和 agent 的稳定入口脚本。每个脚本都应：

- 使用稳定 JSON 输出。
- 在入口处把 sibling `lib/` 加入 `sys.path`。
- 不依赖仓库根 `src/`。
- 不依赖第三方 Python 包。

### `lib/`

`lib/` 中存放可复用的最小公共模块，只保留确定性逻辑：

- `jsonio.py`：统一 JSON 输出。
- `frontmatter.py`：frontmatter 受限子集解析与规范化写回。
- `lark_cli.py`：`lark-cli` JSON 调用封装。
- `doc_binding.py`：文档绑定解析。
- `git_sync.py`：sync trailer、基线发现与 commit 逻辑。
- `comments.py`：评论读取、筛选、payload 组装。
- `journal.py`：`.git/markdown-larkdoc-sync/` 下的运行 journal。

### `references/`

`references/` 只存补充说明，不承载运行逻辑。安装后这些文件会跟随 skill 一起进入 agent 可见目录，供 SKILL.md 相对引用。

## Frontmatter 受限子集

### 基本原则

- frontmatter 不是通用 YAML。
- frontmatter 是本仓库私有、脚本全权管理的受限子集格式。
- agent 不得手写 frontmatter，也不得自行解析 frontmatter。

### 支持的结构

顶层只支持 mapping，允许的顶层键白名单：

- `title`
- `markdown_larkdoc_sync`

`markdown_larkdoc_sync` 只支持 mapping，允许的子键白名单：

- `doc`
- `as`
- `profile`

### 支持的值类型

- `title`：字符串
- `doc`：字符串
- `as`：字符串，仅允许 `user` 或 `bot`
- `profile`：字符串
- `null` 可被解析，但写回时默认不主动生成空值字段

### 明确不支持

- list / tuple / set
- 多行 block scalar
- YAML anchor / alias
- YAML tag
- 自动日期类型推断
- 任意额外顶层键
- 任意额外 `markdown_larkdoc_sync` 子键

### 规范化写回格式

脚本写回时统一重写为固定格式，不承诺保留用户原始风格：

```yaml
---
title: Example
markdown_larkdoc_sync:
  doc: https://example.feishu.cn/wiki/AbCdEfGh
  as: user
  profile: default
---

# Body
```

规则：

- 顶层键顺序固定。
- `markdown_larkdoc_sync` 子键顺序固定。
- 固定两空格缩进。
- 固定 `---` 包裹和单个空行分隔正文。

## Frontmatter 脚本契约

### `bin/read_frontmatter_binding.py`

输入：

- Markdown 文件路径

输出 JSON：

- `frontmatter`
- `binding`
- `body`

行为：

- 使用受限子集 parser。
- 如果 frontmatter 超出支持范围，直接报错。
- `binding` 只暴露 `doc`、`as`、`profile`。

### `bin/write_frontmatter_binding.py`

输入：

- Markdown 文件路径
- `--doc`
- `--as`
- `--profile`
- 可选 `--title`

输出 JSON：

- `markdown_path`
- `frontmatter_written`

行为：

- 如果文件已有受支持 frontmatter，则按规范重写。
- 如果文件无 frontmatter，则创建规范 frontmatter。
- 只写 frontmatter，不负责生成业务正文。

### `bin/extract_markdown_body.py`

输入：

- Markdown 文件路径

输出 JSON：

- `frontmatter`
- `body`

行为：

- 与 `frontmatter.py` 使用同一套受限子集 parser。
- 仅用于正文提取，不单独承担绑定语义校验。

## 其他脚本契约

### `bin/resolve_doc_key.py`

输入：

- 已声明的 `doc` 引用字符串

输出 JSON：

- `declared_doc`
- `resolved_doc_token`
- `resolved_file_type`
- `doc_key`

### `bin/find_last_sync_commit.py`

输入：

- `markdown_path`
- `doc_key`

输出 JSON：

- `status`
- `doc_key`
- `commit`
- `markdown_path`
- `reason`

### `bin/fetch_open_comments.py`

输入：

- `file_token`
- `file_type`

输出 JSON：

- `items`

行为：

- 调用真实 `lark-cli drive file.comments list` 所要求的完整参数。
- 解开 `lark-cli` 响应中的 `data.items`。
- 仅返回未解决评论。
- 保留 `reply_list.replies` 等后续工作流需要的信息。

### `bin/resolve_all_comments.py`

输入：

- `file_token`
- `file_type`

输出 JSON：

- `resolved_comment_ids`
- `results`

行为：

- 脚本内部先调用评论列表接口，收集当前文档全部未解决评论。
- 再逐条调用 patch 接口解决这些评论。
- 不再要求调用方传入 `comment_ids`。
- 其语义必须和名字一致，即“解决当前文档全部未解决评论”。

### `bin/create_sync_commit.py`

输入：

- `markdown_path`
- `declared_doc`
- `identity`
- `resolved_file_type`
- `resolved_doc_token`
- `profile`

输出 JSON：

- `commit`

## Skill 文档要求

`skills/markdown-larkdoc-sync/SKILL.md` 必须满足以下要求：

- 只描述一个手动触发的同步工作流。
- 对所有已经脚本化的确定性步骤都明确写出脚本名。
- 明确要求：agent 不得手改 frontmatter，不得自行解析 frontmatter。
- 明确要求：读取绑定必须调用 `bin/read_frontmatter_binding.py`。
- 明确要求：修改绑定必须调用 `bin/write_frontmatter_binding.py`。
- 明确要求：收尾阶段必须调用 `bin/resolve_all_comments.py` 解决当前全部未解决评论。

推荐执行顺序：

1. 调用 `bin/read_frontmatter_binding.py`
2. 调用 `bin/extract_markdown_body.py`
3. 调用 `bin/resolve_doc_key.py`
4. 调用 `bin/find_last_sync_commit.py`
5. 读取 remote 正文，并调用 `bin/fetch_open_comments.py`
6. 做正文三方合并
7. 把评论转成 review patch
8. 调用 sub-agent 做一致性审校
9. 回写飞书并验证
10. 调用 `bin/resolve_all_comments.py`
11. 调用 `bin/create_sync_commit.py`

## README 要求

### `README.zh.md`

应覆盖：

- 仓库定位：这是一个 `skills` source repository。
- 当前仓库地址：`Piasy/lark-skills`。
- 远程安装命令。
- 单 skill 安装命令。
- 本地开发安装命令。
- 不需要先手动 clone 远程仓库。
- `skills` 工具负责下载仓库、扫描 `SKILL.md` 并安装到 agent skills 目录。
- 不依赖额外 Python 第三方包。
- frontmatter 是受限子集，不是通用 YAML。
- 当前 skills 列表。
- MIT License。

### `README.md`

作为英文镜像版，保留同等安装与使用信息，但内容可更精简。

## 测试与验证策略

### 测试结构

- 根 `tests/` 按 skill 子目录组织，例如 `tests/markdown-larkdoc-sync/`。
- `markdown-larkdoc-sync` 的测试对象改为 `skills/markdown-larkdoc-sync/bin/` 和 `lib/`。
- 所有脚本 smoke test 都以 skill 目录内入口为准。
- frontmatter 相关测试应覆盖：
  - 合法受限子集解析
  - 非法结构拒绝
  - 规范化写回

### 手动验证命令

```bash
python3 -m pytest -q
npx skills add . -g -y --list
npx skills add . -g -y --skill markdown-larkdoc-sync --agent '*'
npx skills list -g --json
```

### 删除 `PyYAML` 后的验证

- `pyproject.toml` 不再声明 `PyYAML` 运行时依赖。
- 全量测试在没有 `PyYAML` 的环境下仍应通过。

## 迁移计划

1. 在 `skills/markdown-larkdoc-sync/` 下创建 `bin/`、`lib/`、`references/`。
2. 把现有仓库根脚本与公共模块迁移到 `bin/` 和 `lib/`。
3. 实现 frontmatter 受限子集 parser / writer，并新增读写绑定脚本。
4. 更新评论相关脚本，使其语义与设计工作流一致。
5. 更新 `SKILL.md`，显式列出脚本化步骤与 frontmatter 约束。
6. 新增 `README.md`、`README.zh.md` 和 `LICENSE`。
7. 把根 `scripts/` 与 `src/` 删除。
8. 把根 `tests/` 重组为按 skill 子目录组织的结构，并更新测试目标路径。
9. 完成全量验证。

## 风险与缓解

### 风险 1：frontmatter 兼容性收缩

- 风险：已有文档若使用复杂 YAML 语法，将在新 parser 下被拒绝。
- 缓解：通过 `write_frontmatter_binding.py` 提供规范化写回路径，并在 README 中明确约束。

### 风险 2：安装后相对 import 失效

- 风险：`bin/` 与 `lib/` 的相对导入若处理不当，安装后脚本无法运行。
- 缓解：所有入口脚本在运行时显式加入 sibling `lib/` 到 `sys.path`，并用 smoke test 覆盖。

### 风险 3：双真相源漂移

- 风险：如果保留根 `scripts/` 与 `src/`，未来容易出现发布版与开发版逻辑不一致。
- 缓解：迁移完成后删除根 `scripts/` 与 `src/`。

### 风险 4：`skills` 工具未来行为变化

- 风险：不同版本 `skills` 工具支持的 agent 集合可能变化。
- 缓解：不在仓库内硬编码 agent 矩阵，README 统一说明兼容性由本机 `skills` 工具版本决定。

## 验收标准

- `npx skills add Piasy/lark-skills -g -y` 可作为推荐安装方式写入 README。
- 安装后的 skill 目录包含 `SKILL.md`、`agents/`、`bin/`、`lib/`、`references/`。
- `markdown-larkdoc-sync` 不再依赖 `PyYAML`。
- frontmatter 读取与修改全部通过脚本执行，并严格遵守受限子集。
- `resolve_all_comments.py` 语义与脚本命名一致，会自动解决当前全部未解决评论。
- `SKILL.md`、README 与脚本契约一致，不再出现“步骤描述与脚本语义不一致”的情况。
- 全量测试通过。
