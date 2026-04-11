# Lark Skills Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将仓库改造成可被 `npx skills add Piasy/lark-skills` 直接安装的 `skills` source repository，并让 `markdown-larkdoc-sync` 在安装后仅依赖 `skills/markdown-larkdoc-sync/` 内资产即可运行。

**Architecture:** 采用单一运行时真相源结构：所有执行入口放在 `skills/markdown-larkdoc-sync/bin/`，共享逻辑放在 `skills/markdown-larkdoc-sync/lib/`。frontmatter 使用 `lib/frontmatter.py` 的受限子集解析与规范化写回，绑定读取与修改分别经 `bin/read_frontmatter_binding.py`、`bin/write_frontmatter_binding.py`。迁移完成后删除仓库根 `scripts/` 与 `src/`，并把测试重组到 `tests/markdown-larkdoc-sync/`。

**Tech Stack:** Python 3.11+、pytest、git、npx skills CLI、lark-cli、Markdown

---

## 文件地图

- `skills/markdown-larkdoc-sync/bin/extract_markdown_body.py`：正文提取入口，复用受限 frontmatter parser。
- `skills/markdown-larkdoc-sync/bin/read_frontmatter_binding.py`：读取 frontmatter 与绑定字段。
- `skills/markdown-larkdoc-sync/bin/write_frontmatter_binding.py`：规范化写回绑定 frontmatter。
- `skills/markdown-larkdoc-sync/bin/resolve_doc_key.py`：解析 `doc` 到 `doc_key`。
- `skills/markdown-larkdoc-sync/bin/find_last_sync_commit.py`：查找最后同步基线。
- `skills/markdown-larkdoc-sync/bin/fetch_open_comments.py`：读取未解决评论。
- `skills/markdown-larkdoc-sync/bin/resolve_all_comments.py`：自动解决全部未解决评论。
- `skills/markdown-larkdoc-sync/bin/create_sync_commit.py`：创建 sync commit。
- `skills/markdown-larkdoc-sync/lib/frontmatter.py`：受限 frontmatter parser 和 writer。
- `skills/markdown-larkdoc-sync/lib/jsonio.py`：统一 JSON 输出。
- `skills/markdown-larkdoc-sync/lib/lark_cli.py`：`lark-cli` 调用封装。
- `skills/markdown-larkdoc-sync/lib/doc_binding.py`：文档绑定解析。
- `skills/markdown-larkdoc-sync/lib/git_sync.py`：sync trailer 相关逻辑。
- `skills/markdown-larkdoc-sync/lib/comments.py`：评论过滤与 resolve payload。
- `skills/markdown-larkdoc-sync/lib/journal.py`：运行 journal。
- `skills/markdown-larkdoc-sync/references/frontmatter-subset.md`：frontmatter 受限子集文档。
- `skills/markdown-larkdoc-sync/references/installation.md`：安装与前置说明。
- `README.zh.md`：中文仓库说明。
- `README.md`：英文仓库说明。
- `LICENSE`：MIT。
- `tests/markdown-larkdoc-sync/`：按 skill 组织的测试。

### Task 1: 建立 skill 内运行时骨架并迁移现有模块

**Files:**
- Create: `skills/markdown-larkdoc-sync/bin/resolve_doc_key.py`
- Create: `skills/markdown-larkdoc-sync/bin/find_last_sync_commit.py`
- Create: `skills/markdown-larkdoc-sync/bin/fetch_open_comments.py`
- Create: `skills/markdown-larkdoc-sync/bin/resolve_all_comments.py`
- Create: `skills/markdown-larkdoc-sync/bin/create_sync_commit.py`
- Create: `skills/markdown-larkdoc-sync/lib/__init__.py`
- Create: `skills/markdown-larkdoc-sync/lib/jsonio.py`
- Create: `skills/markdown-larkdoc-sync/lib/lark_cli.py`
- Create: `skills/markdown-larkdoc-sync/lib/doc_binding.py`
- Create: `skills/markdown-larkdoc-sync/lib/git_sync.py`
- Create: `skills/markdown-larkdoc-sync/lib/comments.py`
- Create: `skills/markdown-larkdoc-sync/lib/journal.py`
- Create: `tests/markdown-larkdoc-sync/conftest.py`
- Create: `tests/markdown-larkdoc-sync/test_layout_contract.py`

- [x] **Step 1: 先写失败测试，锁定运行时必须在 skill 目录内**

```python
# tests/markdown-larkdoc-sync/test_layout_contract.py
from pathlib import Path


SKILL_ROOT = Path('skills/markdown-larkdoc-sync')


def test_runtime_layout_contains_required_bin_and_lib_files():
    expected = {
        'bin/resolve_doc_key.py',
        'bin/find_last_sync_commit.py',
        'bin/fetch_open_comments.py',
        'bin/resolve_all_comments.py',
        'bin/create_sync_commit.py',
        'lib/__init__.py',
        'lib/jsonio.py',
        'lib/lark_cli.py',
        'lib/doc_binding.py',
        'lib/git_sync.py',
        'lib/comments.py',
        'lib/journal.py',
    }

    missing = [rel for rel in sorted(expected) if not (SKILL_ROOT / rel).exists()]
    assert missing == []
```

```python
# tests/markdown-larkdoc-sync/conftest.py
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
```

- [x] **Step 2: 运行测试，确认骨架尚未完成**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_layout_contract.py -q`
Expected: FAIL，提示缺少 `bin/*` 与 `lib/*`。

- [x] **Step 3: 创建目录并迁移现有脚本与模块到 skill 目录**

```bash
mkdir -p skills/markdown-larkdoc-sync/bin skills/markdown-larkdoc-sync/lib tests/markdown-larkdoc-sync
cp src/markdown_larkdoc_sync/jsonio.py skills/markdown-larkdoc-sync/lib/jsonio.py
cp src/markdown_larkdoc_sync/lark_cli.py skills/markdown-larkdoc-sync/lib/lark_cli.py
cp src/markdown_larkdoc_sync/doc_binding.py skills/markdown-larkdoc-sync/lib/doc_binding.py
cp src/markdown_larkdoc_sync/git_sync.py skills/markdown-larkdoc-sync/lib/git_sync.py
cp src/markdown_larkdoc_sync/comments.py skills/markdown-larkdoc-sync/lib/comments.py
cp src/markdown_larkdoc_sync/journal.py skills/markdown-larkdoc-sync/lib/journal.py
cp scripts/resolve_doc_key.py skills/markdown-larkdoc-sync/bin/resolve_doc_key.py
cp scripts/find_last_sync_commit.py skills/markdown-larkdoc-sync/bin/find_last_sync_commit.py
cp scripts/fetch_open_comments.py skills/markdown-larkdoc-sync/bin/fetch_open_comments.py
cp scripts/resolve_all_comments.py skills/markdown-larkdoc-sync/bin/resolve_all_comments.py
cp scripts/create_sync_commit.py skills/markdown-larkdoc-sync/bin/create_sync_commit.py
printf '__all__ = []\n' > skills/markdown-larkdoc-sync/lib/__init__.py
```

```python
# 统一替换 skill 内模块导入方式
# skills/markdown-larkdoc-sync/lib/doc_binding.py
from lark_cli import LarkCLI

# skills/markdown-larkdoc-sync/lib/journal.py
from jsonio import dump_json
```

```python
# skills/markdown-larkdoc-sync/bin/*.py 入口统一模板
SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
```

- [x] **Step 4: 运行布局测试，确认骨架可见**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_layout_contract.py -q`
Expected: PASS with `1 passed`.

- [x] **Step 5: 提交骨架迁移**

```bash
git add skills/markdown-larkdoc-sync/bin skills/markdown-larkdoc-sync/lib tests/markdown-larkdoc-sync/conftest.py tests/markdown-larkdoc-sync/test_layout_contract.py
git commit -m 'refactor: initialize skill-local runtime layout'
```

### Task 2: 实现 frontmatter 受限子集与绑定读写脚本

**Files:**
- Create: `skills/markdown-larkdoc-sync/lib/frontmatter.py`
- Create: `skills/markdown-larkdoc-sync/bin/read_frontmatter_binding.py`
- Create: `skills/markdown-larkdoc-sync/bin/write_frontmatter_binding.py`
- Create: `skills/markdown-larkdoc-sync/bin/extract_markdown_body.py`
- Create: `tests/markdown-larkdoc-sync/test_frontmatter_contract.py`

- [x] **Step 1: 先写失败测试，锁定 parser、writer 与 CLI 契约**

```python
# tests/markdown-larkdoc-sync/test_frontmatter_contract.py
import json
import subprocess
import sys
from pathlib import Path

import pytest

from frontmatter import FrontmatterError, parse_frontmatter, split_frontmatter, write_frontmatter_to_text


ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'bin'


def test_parse_frontmatter_accepts_whitelisted_mapping_only():
    payload = parse_frontmatter(
        'title: Example\n'
        'markdown_larkdoc_sync:\n'
        '  doc: https://example.feishu.cn/wiki/AbCd\n'
        '  as: user\n'
        '  profile: default\n'
    )

    assert payload['title'] == 'Example'
    assert payload['markdown_larkdoc_sync']['as'] == 'user'


def test_parse_frontmatter_rejects_sequence_and_unknown_key():
    with pytest.raises(FrontmatterError):
        parse_frontmatter('title:\n- bad\n')

    with pytest.raises(FrontmatterError):
        parse_frontmatter('unexpected: x\n')


def test_split_frontmatter_and_body_contract():
    frontmatter, body = split_frontmatter('---\ntitle: A\n---\n\n# Body\n')

    assert frontmatter == {'title': 'A'}
    assert body == '# Body\n'


def test_write_frontmatter_uses_canonical_order_and_spacing():
    rendered = write_frontmatter_to_text(
        body='# Body\n',
        title='Example',
        doc='https://example.feishu.cn/wiki/AbCd',
        identity='bot',
        profile='p1',
    )

    assert rendered.startswith(
        '---\n'
        'title: Example\n'
        'markdown_larkdoc_sync:\n'
        '  doc: https://example.feishu.cn/wiki/AbCd\n'
        '  as: bot\n'
        '  profile: p1\n'
        '---\n\n'
    )


def test_read_and_write_binding_cli_contract(tmp_path: Path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('# Body\n', encoding='utf-8')

    subprocess.run(
        [
            sys.executable,
            str(BIN / 'write_frontmatter_binding.py'),
            str(markdown),
            '--doc',
            'https://example.feishu.cn/wiki/AbCd',
            '--as',
            'user',
            '--profile',
            'default',
            '--title',
            'Example',
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    result = subprocess.run(
        [sys.executable, str(BIN / 'read_frontmatter_binding.py'), str(markdown)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    payload = json.loads(result.stdout)

    assert sorted(payload.keys()) == ['binding', 'body', 'frontmatter']
    assert payload['binding'] == {
        'doc': 'https://example.feishu.cn/wiki/AbCd',
        'as': 'user',
        'profile': 'default',
    }
    assert payload['body'] == '# Body\n'
```

- [x] **Step 2: 运行测试，确认 frontmatter 新能力尚未实现**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_frontmatter_contract.py -q`
Expected: FAIL，提示 `frontmatter` 模块或脚本不存在。

- [x] **Step 3: 实现 frontmatter 受限子集 parser/writer 与三个 CLI**

```python
# skills/markdown-larkdoc-sync/lib/frontmatter.py
from __future__ import annotations

from dataclasses import dataclass
import re


ALLOWED_TOP_KEYS = ('title', 'markdown_larkdoc_sync')
ALLOWED_BINDING_KEYS = ('doc', 'as', 'profile')
ALLOWED_AS = ('user', 'bot')
_FRONTMATTER_PATTERN = re.compile(r'^---(?:\r?\n)(.*?)(?:\r?\n)---(?:\r?\n|$)', re.DOTALL)


class FrontmatterError(ValueError):
    pass


@dataclass(frozen=True)
class Binding:
    doc: str | None
    identity: str | None
    profile: str | None


def _parse_scalar(raw: str) -> str | None:
    value = raw.strip()
    if value in ('null', 'Null', 'NULL', '~'):
        return None
    if not value:
        return None
    if value[0] in {'"', "'"} and value[-1] == value[0] and len(value) >= 2:
        return value[1:-1]
    return value


def parse_frontmatter(frontmatter_text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_nested: dict[str, str | None] | None = None

    for raw_line in frontmatter_text.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith(('-', '[', ']')):
            raise FrontmatterError('unsupported sequence style in frontmatter')

        indent = len(raw_line) - len(raw_line.lstrip(' '))
        line = raw_line.strip()
        if ':' not in line:
            raise FrontmatterError('invalid frontmatter line')
        key, value = line.split(':', 1)
        key = key.strip()

        if indent == 0:
            if key not in ALLOWED_TOP_KEYS:
                raise FrontmatterError(f'unsupported top-level key: {key}')
            if key == 'markdown_larkdoc_sync':
                if value.strip():
                    raise FrontmatterError('markdown_larkdoc_sync must be a mapping')
                nested: dict[str, str | None] = {}
                result[key] = nested
                current_nested = nested
            else:
                parsed = _parse_scalar(value)
                if parsed is not None and not isinstance(parsed, str):
                    raise FrontmatterError('title must be string or null')
                result[key] = parsed
                current_nested = None
            continue

        if indent == 2 and current_nested is not None:
            if key not in ALLOWED_BINDING_KEYS:
                raise FrontmatterError(f'unsupported binding key: {key}')
            parsed = _parse_scalar(value)
            if parsed is not None and not isinstance(parsed, str):
                raise FrontmatterError(f'{key} must be string or null')
            current_nested[key] = parsed
            continue

        raise FrontmatterError('unsupported indentation structure in frontmatter')

    binding = result.get('markdown_larkdoc_sync')
    if isinstance(binding, dict):
        as_value = binding.get('as')
        if as_value is not None and as_value not in ALLOWED_AS:
            raise FrontmatterError('as must be user or bot')
    return result


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONTMATTER_PATTERN.match(text)
    if match is None:
        return {}, text

    frontmatter_text = match.group(1)
    body = text[match.end():].lstrip('\r\n')
    return parse_frontmatter(frontmatter_text), body


def extract_binding(frontmatter: dict[str, object]) -> Binding:
    nested = frontmatter.get('markdown_larkdoc_sync')
    if not isinstance(nested, dict):
        return Binding(doc=None, identity=None, profile=None)
    return Binding(
        doc=nested.get('doc') if isinstance(nested.get('doc'), str) else None,
        identity=nested.get('as') if isinstance(nested.get('as'), str) else None,
        profile=nested.get('profile') if isinstance(nested.get('profile'), str) else None,
    )


def _serialize_scalar(value: str | None) -> str:
    if value is None:
        return 'null'
    return value


def render_frontmatter(title: str | None, doc: str | None, identity: str | None, profile: str | None) -> str:
    lines = ['---']
    if title is not None:
        lines.append(f'title: {_serialize_scalar(title)}')
    lines.append('markdown_larkdoc_sync:')
    if doc is not None:
        lines.append(f'  doc: {_serialize_scalar(doc)}')
    if identity is not None:
        lines.append(f'  as: {_serialize_scalar(identity)}')
    if profile is not None:
        lines.append(f'  profile: {_serialize_scalar(profile)}')
    lines.append('---')
    return '\n'.join(lines)


def write_frontmatter_to_text(
    *,
    body: str,
    title: str | None,
    doc: str,
    identity: str,
    profile: str,
) -> str:
    if identity not in ALLOWED_AS:
        raise FrontmatterError('as must be user or bot')
    head = render_frontmatter(title=title, doc=doc, identity=identity, profile=profile)
    normalized_body = body if body.endswith('\n') or body == '' else f'{body}\n'
    return f'{head}\n\n{normalized_body}'
```

```python
# skills/markdown-larkdoc-sync/bin/read_frontmatter_binding.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from frontmatter import extract_binding, split_frontmatter
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    args = parser.parse_args()

    text = Path(args.markdown_path).read_text(encoding='utf-8')
    frontmatter, body = split_frontmatter(text)
    binding = extract_binding(frontmatter)
    dump_json(
        {
            'frontmatter': frontmatter,
            'binding': {'doc': binding.doc, 'as': binding.identity, 'profile': binding.profile},
            'body': body,
        },
        sys.stdout,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

```python
# skills/markdown-larkdoc-sync/bin/write_frontmatter_binding.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from frontmatter import split_frontmatter, write_frontmatter_to_text
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('--doc', required=True)
    parser.add_argument('--as', dest='identity', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--title')
    args = parser.parse_args()

    markdown_path = Path(args.markdown_path)
    text = markdown_path.read_text(encoding='utf-8') if markdown_path.exists() else ''
    _, body = split_frontmatter(text)

    content = write_frontmatter_to_text(
        body=body,
        title=args.title,
        doc=args.doc,
        identity=args.identity,
        profile=args.profile,
    )
    markdown_path.write_text(content, encoding='utf-8')

    dump_json(
        {
            'markdown_path': args.markdown_path,
            'frontmatter_written': {
                'title': args.title,
                'markdown_larkdoc_sync': {
                    'doc': args.doc,
                    'as': args.identity,
                    'profile': args.profile,
                },
            },
        },
        sys.stdout,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

```python
# skills/markdown-larkdoc-sync/bin/extract_markdown_body.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from frontmatter import split_frontmatter
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    args = parser.parse_args()

    text = Path(args.markdown_path).read_text(encoding='utf-8')
    frontmatter, body = split_frontmatter(text)
    dump_json({'frontmatter': frontmatter, 'body': body}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [x] **Step 4: 运行 frontmatter 测试，确认契约通过**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_frontmatter_contract.py -q`
Expected: PASS。

- [x] **Step 5: 提交 frontmatter 与绑定入口实现**

```bash
git add skills/markdown-larkdoc-sync/lib/frontmatter.py skills/markdown-larkdoc-sync/bin/read_frontmatter_binding.py skills/markdown-larkdoc-sync/bin/write_frontmatter_binding.py skills/markdown-larkdoc-sync/bin/extract_markdown_body.py tests/markdown-larkdoc-sync/test_frontmatter_contract.py
git commit -m 'feat: add restricted frontmatter parser and binding scripts'
```

### Task 3: 更新其余脚本契约并统一测试目标到 skill 入口

**Files:**
- Modify: `tests/markdown-larkdoc-sync/test_cli_smoke_contracts.py`
- Modify: `tests/markdown-larkdoc-sync/test_doc_binding.py`
- Modify: `tests/markdown-larkdoc-sync/test_git_sync.py`
- Modify: `tests/markdown-larkdoc-sync/test_comments.py`
- Modify: `tests/markdown-larkdoc-sync/test_lark_cli.py`
- Modify: `tests/markdown-larkdoc-sync/test_jsonio.py`
- Modify: `tests/markdown-larkdoc-sync/test_journal.py`

- [x] **Step 1: 先把现有测试移动到按 skill 分组目录**

```bash
git mv tests/test_cli_smoke_contracts.py tests/markdown-larkdoc-sync/test_cli_smoke_contracts.py
git mv tests/test_doc_binding.py tests/markdown-larkdoc-sync/test_doc_binding.py
git mv tests/test_git_sync.py tests/markdown-larkdoc-sync/test_git_sync.py
git mv tests/test_comments.py tests/markdown-larkdoc-sync/test_comments.py
git mv tests/test_lark_cli.py tests/markdown-larkdoc-sync/test_lark_cli.py
git mv tests/test_jsonio.py tests/markdown-larkdoc-sync/test_jsonio.py
git mv tests/test_journal.py tests/markdown-larkdoc-sync/test_journal.py
git mv tests/test_markdown_body.py tests/markdown-larkdoc-sync/test_markdown_body.py
```

- [x] **Step 2: 更新测试导入路径与脚本路径，先让它失败一次**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_cli_smoke_contracts.py -q`
Expected: FAIL，提示仍引用旧 `scripts/` 或旧模块路径。

- [x] **Step 3: 修改测试为 skill 入口契约**

```python
# tests/markdown-larkdoc-sync/test_cli_smoke_contracts.py 关键常量
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'bin'

# 执行脚本
result = subprocess.run(
    [sys.executable, str(BIN / script_name), *args],
    cwd=cwd,
    check=True,
    capture_output=True,
    text=True,
    env=env,
)
```

```python
# tests/markdown-larkdoc-sync/test_doc_binding.py 导入
from doc_binding import resolve_declared_doc

# tests/markdown-larkdoc-sync/test_comments.py 导入
from comments import build_resolve_payload, flatten_open_comments

# tests/markdown-larkdoc-sync/test_git_sync.py 导入
from git_sync import build_sync_message, classify_candidates, find_last_sync_commit
```

- [x] **Step 4: 运行模块与脚本合同测试**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_cli_smoke_contracts.py tests/markdown-larkdoc-sync/test_doc_binding.py tests/markdown-larkdoc-sync/test_git_sync.py tests/markdown-larkdoc-sync/test_comments.py -q`
Expected: PASS。

- [x] **Step 5: 提交测试迁移与契约更新**

```bash
git add tests/markdown-larkdoc-sync
git commit -m 'test: migrate contracts to skill-local bin and lib'
```

### Task 4: 更新 SKILL 文档与 references 说明

**Files:**
- Modify: `skills/markdown-larkdoc-sync/SKILL.md`
- Create: `skills/markdown-larkdoc-sync/references/frontmatter-subset.md`
- Create: `skills/markdown-larkdoc-sync/references/installation.md`
- Modify: `tests/test_skill_docs.py`

- [x] **Step 1: 先写失败测试，锁定 SKILL 必须声明的新约束**

```python
# tests/test_skill_docs.py
from pathlib import Path


def test_skill_mentions_frontmatter_and_script_contracts():
    content = Path('skills/markdown-larkdoc-sync/SKILL.md').read_text(encoding='utf-8')

    assert 'agent 不得手改 frontmatter' in content
    assert 'agent 不得自行解析 frontmatter' in content
    assert 'bin/read_frontmatter_binding.py' in content
    assert 'bin/write_frontmatter_binding.py' in content
    assert 'bin/resolve_all_comments.py' in content
```

- [x] **Step 2: 运行文档合同测试，确认当前内容不满足**

Run: `python3 -m pytest tests/test_skill_docs.py -q`
Expected: FAIL。

- [x] **Step 3: 更新 SKILL 和 references**

```markdown
# skills/markdown-larkdoc-sync/SKILL.md 核心改动点
- 所有脚本路径从 `scripts/*` 改为 `bin/*`
- 显式要求读取绑定必须调用 `bin/read_frontmatter_binding.py`
- 显式要求修改绑定必须调用 `bin/write_frontmatter_binding.py`
- 显式声明 frontmatter 只能通过脚本读写
- 推荐执行顺序调整为 spec 要求的 11 步
```

```markdown
# skills/markdown-larkdoc-sync/references/frontmatter-subset.md
- 顶层键白名单：`title`、`markdown_larkdoc_sync`
- 子键白名单：`doc`、`as`、`profile`
- `as` 仅允许 `user`、`bot`
- 明确不支持 list、anchor、tag、多行 block scalar
```

```markdown
# skills/markdown-larkdoc-sync/references/installation.md
- 安装命令：`npx skills add Piasy/lark-skills -g -y`
- 单 skill 安装：`npx skills add Piasy/lark-skills -s markdown-larkdoc-sync -g -y`
- 本地安装：`npx skills add . -g -y`
- 运行前提：`python3 >= 3.11`、`git`、`lark-cli`、已认证
```

- [x] **Step 4: 运行文档合同测试**

Run: `python3 -m pytest tests/test_skill_docs.py -q`
Expected: PASS。

- [ ] **Step 5: 提交文档和 references 更新**

```bash
git add skills/markdown-larkdoc-sync/SKILL.md skills/markdown-larkdoc-sync/references/frontmatter-subset.md skills/markdown-larkdoc-sync/references/installation.md tests/test_skill_docs.py
git commit -m 'docs: align skill workflow and frontmatter constraints'
```

### Task 5: 增加 README 双语说明与 MIT License

**Files:**
- Create: `README.zh.md`
- Create: `README.md`
- Create: `LICENSE`
- Create: `tests/markdown-larkdoc-sync/test_readme_contract.py`

- [x] **Step 1: 先写失败测试，锁定 README 关键信息**

```python
# tests/markdown-larkdoc-sync/test_readme_contract.py
from pathlib import Path


def test_readme_zh_contains_install_and_scope_statements():
    content = Path('README.zh.md').read_text(encoding='utf-8')
    assert 'skills source repository' in content
    assert 'Piasy/lark-skills' in content
    assert 'npx skills add Piasy/lark-skills -g -y' in content
    assert '不需要先手动 clone' in content
    assert 'frontmatter 是受限子集' in content
    assert 'MIT' in content


def test_readme_en_contains_install_and_scope_statements():
    content = Path('README.md').read_text(encoding='utf-8')
    assert 'skills source repository' in content
    assert 'npx skills add Piasy/lark-skills -g -y' in content
    assert 'frontmatter' in content
    assert 'MIT License' in content


def test_mit_license_exists():
    assert 'MIT License' in Path('LICENSE').read_text(encoding='utf-8')
```

- [x] **Step 2: 运行测试，确认文档文件尚未创建**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_readme_contract.py -q`
Expected: FAIL。

- [ ] **Step 3: 编写 README.zh.md、README.md 与 LICENSE**

```markdown
# README.zh.md 最小目录
- 仓库定位（skills source repository）
- 安装命令（全量、单 skill、本地、list）
- 工作原理（skills 工具下载并扫描 `SKILL.md`）
- 运行前提
- frontmatter 受限子集约束
- 当前 skills 列表
- License
```

```markdown
# README.md 最小目录
- Repository purpose
- Install commands
- Runtime prerequisites
- Frontmatter subset constraints
- Current skills
- License
```

```text
# LICENSE
使用标准 MIT License 模板文本。
```

- [ ] **Step 4: 运行 README 合同测试**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_readme_contract.py -q`
Expected: PASS。

- [ ] **Step 5: 提交 README 与 License**

```bash
git add README.zh.md README.md LICENSE tests/markdown-larkdoc-sync/test_readme_contract.py
git commit -m 'docs: add bilingual readme and mit license'
```

### Task 6: 删除根 scripts/src 并清理依赖与测试入口

**Files:**
- Modify: `pyproject.toml`
- Delete: `scripts/`
- Delete: `src/`
- Delete: `tests/conftest.py`
- Modify: `tests/markdown-larkdoc-sync/test_markdown_body.py`
- Create: `tests/markdown-larkdoc-sync/test_repo_boundary_contract.py`

- [ ] **Step 1: 先写失败测试，锁定仓库边界收敛结果**

```python
# tests/markdown-larkdoc-sync/test_repo_boundary_contract.py
from pathlib import Path


def test_root_scripts_and_src_are_removed_after_migration():
    assert not Path('scripts').exists()
    assert not Path('src').exists()


def test_pyproject_has_no_pyyaml_runtime_dependency():
    content = Path('pyproject.toml').read_text(encoding='utf-8')
    assert 'PyYAML' not in content
```

- [ ] **Step 2: 运行边界测试，确认当前仓库还未收敛**

Run: `python3 -m pytest tests/markdown-larkdoc-sync/test_repo_boundary_contract.py -q`
Expected: FAIL。

- [ ] **Step 3: 删除旧目录并清理 pyproject 依赖**

```bash
rm -rf scripts src
rm -f tests/conftest.py
```

```toml
# pyproject.toml
[build-system]
requires = ['setuptools>=68']
build-backend = 'setuptools.build_meta'

[project]
name = 'markdown-larkdoc-sync'
version = '0.1.0'
requires-python = '>=3.11'
dependencies = []

[project.optional-dependencies]
dev = ['pytest>=8.0']

[tool.pytest.ini_options]
addopts = '-q'
testpaths = ['tests']
```

```python
# tests/markdown-larkdoc-sync/test_markdown_body.py
# 迁移后不再测试旧 markdown_body 模块。
# 只保留对 bin/extract_markdown_body.py 与 lib/frontmatter.py 的合同测试。
```

- [ ] **Step 4: 运行全量测试，确认旧路径引用已清除**

Run: `python3 -m pytest -q`
Expected: PASS。

- [ ] **Step 5: 提交边界收敛与依赖清理**

```bash
git add pyproject.toml tests/markdown-larkdoc-sync/test_repo_boundary_contract.py tests/markdown-larkdoc-sync/test_markdown_body.py
git add -A scripts src tests/conftest.py
git commit -m 'refactor: remove root runtime and drop pyyaml dependency'
```

### Task 7: 端到端验证 skills 安装与无 PyYAML 运行

**Files:**
- Modify: `docs/superpowers/specs/2026-04-11-lark-skills-packaging-design.md` (可选，仅在实施偏差时补充实现备注)

- [ ] **Step 1: 运行全量测试**

Run: `python3 -m pytest -q`
Expected: PASS。

- [ ] **Step 2: 本地验证 skills source 能被扫描和安装**

Run: `npx skills add . -g -y --list`
Expected: 输出包含 `markdown-larkdoc-sync`。

Run: `npx skills add . -g -y --skill markdown-larkdoc-sync --agent '*'`
Expected: 安装成功，不报缺少 `scripts/` 或 `src/`。

Run: `npx skills list -g --json`
Expected: 已安装列表包含 `markdown-larkdoc-sync`。

- [ ] **Step 3: 在无 PyYAML 环境验证**

Run: `python3 -m venv .tmp-no-yaml`
Expected: 创建独立虚拟环境。

Run: `. .tmp-no-yaml/bin/activate && pip install -e .[dev] && python -m pytest -q`
Expected: PASS，且测试不依赖 PyYAML。

- [ ] **Step 4: 清理临时环境并提交验证记录**

Run: `rm -rf .tmp-no-yaml`
Expected: 临时目录清理完成。

```bash
git add -A
git commit -m 'chore: verify packaging workflow and test matrix'
```

## Self-Review Checklist

- [ ] Spec coverage: 对照 spec 各章节确认都有对应任务。
- [ ] Placeholder scan: 全文无 TBD、TODO、later 等占位词。
- [ ] Type consistency: `binding.as` 与 CLI `--as` 命名在计划里保持一致。
- [ ] Path consistency: 全部脚本路径均为 `skills/markdown-larkdoc-sync/bin/*`。

## 执行建议

- 若希望更快推进，优先选 `subagent-driven-development`，每个 Task 由独立 sub-agent 执行后主 agent 复核。
- 若希望串行可控，选 `executing-plans` 在当前会话按 Task 顺序执行。
