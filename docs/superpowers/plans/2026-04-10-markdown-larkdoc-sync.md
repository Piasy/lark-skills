# Markdown LarkDoc Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前仓库中交付一个可用的 `markdown-larkdoc-sync` skill 与配套脚本，覆盖 Markdown 正文提取、飞书文档身份解析、Git 同步基线发现、评论读取与解决、专用 sync commit 创建，以及中文技能说明。

**Architecture:** 采用 Python 脚本层加 skill 编排的双层结构。所有确定性逻辑沉淀到 `src/markdown_larkdoc_sync/` 与 `scripts/`，统一输出稳定 JSON；所有需要语义判断的步骤保留在 `skills/markdown-larkdoc-sync/SKILL.md` 中，由父 agent 编排，并在一致性审校阶段强制调用同模型配置的 sub-agent。

**Tech Stack:** Python 3.11+、PyYAML、pytest、subprocess 调用 `git` 与 `lark-cli`、Markdown skill 文档

---

## 文件地图

- `pyproject.toml`：Python 项目与测试配置。
- `.gitignore`：保留 `lark-cli` 忽略规则，并补充 Python 缓存忽略项。
- `src/markdown_larkdoc_sync/jsonio.py`：统一 JSON 输出。
- `src/markdown_larkdoc_sync/markdown_body.py`：frontmatter 拆分、正文提取、代码块安全归一化。
- `src/markdown_larkdoc_sync/lark_cli.py`：`lark-cli` JSON 调用封装。
- `src/markdown_larkdoc_sync/doc_binding.py`：`doc` URL 或 token 解析与 `doc_key` 生成。
- `src/markdown_larkdoc_sync/git_sync.py`：sync trailer 解析、基线查找、sync commit 创建。
- `src/markdown_larkdoc_sync/comments.py`：未解决评论线程拉平与批量 resolve。
- `src/markdown_larkdoc_sync/journal.py`：`.git/markdown-larkdoc-sync/` 运行 journal 写入。
- `scripts/extract_markdown_body.py`：输出 `{frontmatter, body}`。
- `scripts/resolve_doc_key.py`：输出 `{declared_doc, resolved_doc_token, resolved_file_type, doc_key}`。
- `scripts/find_last_sync_commit.py`：输出 `{status, doc_key, commit, markdown_path, reason}`。
- `scripts/create_sync_commit.py`：创建专用 sync commit，并输出最新 commit SHA。
- `scripts/fetch_open_comments.py`：拉取并展开当前未解决评论线程。
- `scripts/resolve_all_comments.py`：解决当前所有未解决评论。
- `skills/markdown-larkdoc-sync/SKILL.md`：中文 skill 主说明。
- `skills/markdown-larkdoc-sync/agents/openai.yaml`：skill 元数据。
- `tests/`：脚本层、Git 合同、skill 文本合同与 smoke tests。

### Task 1: 建立 Python 骨架与稳定 JSON 输出

**Files:**
- Create: `pyproject.toml`
- Create: `src/markdown_larkdoc_sync/__init__.py`
- Create: `src/markdown_larkdoc_sync/jsonio.py`
- Create: `tests/conftest.py`
- Create: `tests/test_jsonio.py`
- Modify: `.gitignore`

- [ ] **Step 1: 先写失败测试，锁定 JSON 输出契约**

```python
# tests/test_jsonio.py
import io
import json

from markdown_larkdoc_sync.jsonio import dump_json


def test_dump_json_is_utf8_sorted_and_newline_terminated():
    buffer = io.StringIO()

    dump_json({'z': 1, 'a': '中文'}, buffer)

    payload = json.loads(buffer.getvalue())
    assert payload == {'a': '中文', 'z': 1}
    assert buffer.getvalue().index('a') < buffer.getvalue().index('z')
    assert buffer.getvalue().endswith('\n')
```

- [ ] **Step 2: 运行测试，确认当前仓库还没有实现**

Run: `python3 -m pytest tests/test_jsonio.py -q`
Expected: FAIL with import error for `markdown_larkdoc_sync`

- [ ] **Step 3: 写最小可用实现与项目配置**

```toml
# pyproject.toml
[build-system]
requires = ['setuptools>=68']
build-backend = 'setuptools.build_meta'

[project]
name = 'markdown-larkdoc-sync'
version = '0.1.0'
requires-python = '>=3.11'
dependencies = ['PyYAML>=6.0']

[project.optional-dependencies]
dev = ['pytest>=8.0']

[tool.pytest.ini_options]
addopts = '-q'
testpaths = ['tests']
```

```gitignore
# .gitignore
lark-cli
.venv
.pytest_cache
__pycache__
```

```python
# src/markdown_larkdoc_sync/__init__.py
__all__ = []
```

```python
# src/markdown_larkdoc_sync/jsonio.py
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, TextIO


def dump_json(payload: Mapping[str, Any], stream: TextIO) -> None:
    json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write('\n')
```

```python
# tests/conftest.py
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

- [ ] **Step 4: 重新运行测试，确认基础设施通过**

Run: `python3 -m pytest tests/test_jsonio.py -q`
Expected: PASS with `1 passed`

- [ ] **Step 5: 提交第一个可工作的 Python 骨架**

```bash
git add .gitignore pyproject.toml src/markdown_larkdoc_sync/__init__.py src/markdown_larkdoc_sync/jsonio.py tests/conftest.py tests/test_jsonio.py
git commit -m 'chore: bootstrap python package and json helpers' -- .gitignore pyproject.toml src/markdown_larkdoc_sync/__init__.py src/markdown_larkdoc_sync/jsonio.py tests/conftest.py tests/test_jsonio.py
```

### Task 2: 实现 Markdown frontmatter 拆分与正文提取脚本

**Files:**
- Create: `src/markdown_larkdoc_sync/markdown_body.py`
- Create: `scripts/extract_markdown_body.py`
- Create: `tests/test_markdown_body.py`

- [ ] **Step 1: 先写失败测试，覆盖 frontmatter、正文归一化与 CLI 输出**

```python
# tests/test_markdown_body.py
import json
import subprocess
import sys

from markdown_larkdoc_sync.markdown_body import normalize_body, split_frontmatter


def test_split_frontmatter_returns_mapping_and_body():
    frontmatter, body = split_frontmatter(
        '---\nmarkdown_larkdoc_sync:\n  doc: https://example/wiki/x\n---\n\n# Title\n'
    )

    assert frontmatter['markdown_larkdoc_sync']['doc'].endswith('/x')
    assert body == '# Title\n'


def test_normalize_body_keeps_mermaid_block_literal():
    body = '# T\n\n```mermaid\nflowchart TD\nA-->B\n```\n\n'

    assert normalize_body(body) == '# T\n\n```mermaid\nflowchart TD\nA-->B\n```\n'


def test_extract_markdown_body_cli_smoke(tmp_path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('---\ntitle: 示例\n---\n\n# Title\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, 'scripts/extract_markdown_body.py', str(markdown)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload['frontmatter']['title'] == '示例'
    assert payload['body'] == '# Title\n'
```

- [ ] **Step 2: 运行测试，确认解析逻辑尚未存在**

Run: `python3 -m pytest tests/test_markdown_body.py -q`
Expected: FAIL with import error for `markdown_body`

- [ ] **Step 3: 实现 frontmatter 拆分、正文归一化与 CLI**

```python
# src/markdown_larkdoc_sync/markdown_body.py
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith('---\n'):
        return {}, text

    marker = '\n---\n'
    end = text.find(marker, 4)
    if end == -1:
        return {}, text

    frontmatter_text = text[4:end]
    body = text[end + len(marker):]
    data = yaml.safe_load(frontmatter_text) or {}
    return data, body.lstrip('\n')


def normalize_body(body: str) -> str:
    normalized: list[str] = []
    in_fence = False

    for line in body.splitlines():
        if line.startswith('```'):
            in_fence = not in_fence
            normalized.append(line)
            continue
        normalized.append(line if in_fence else line.rstrip())

    return '\n'.join(normalized).rstrip() + '\n'


def read_markdown_parts(path: Path) -> tuple[dict[str, Any], str]:
    return split_frontmatter(path.read_text(encoding='utf-8'))
```

```python
# scripts/extract_markdown_body.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.markdown_body import normalize_body, read_markdown_parts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    args = parser.parse_args()

    frontmatter, body = read_markdown_parts(Path(args.markdown_path))
    dump_json({'frontmatter': frontmatter, 'body': normalize_body(body)}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 4: 运行正文提取测试，确认解析与 CLI 一并通过**

Run: `python3 -m pytest tests/test_markdown_body.py -q`
Expected: PASS with `3 passed`

- [ ] **Step 5: 提交 Markdown 正文提取能力**

```bash
git add src/markdown_larkdoc_sync/markdown_body.py scripts/extract_markdown_body.py tests/test_markdown_body.py
git commit -m 'feat: add markdown body extraction script' -- src/markdown_larkdoc_sync/markdown_body.py scripts/extract_markdown_body.py tests/test_markdown_body.py
```

### Task 3: 实现飞书绑定解析与 `doc_key` 脚本

**Files:**
- Create: `src/markdown_larkdoc_sync/lark_cli.py`
- Create: `src/markdown_larkdoc_sync/doc_binding.py`
- Create: `scripts/resolve_doc_key.py`
- Create: `tests/test_doc_binding.py`

- [ ] **Step 1: 先写失败测试，覆盖 docx URL、wiki URL、原始 token 与 CLI 合同**

```python
# tests/test_doc_binding.py
import json
import subprocess
import sys

from markdown_larkdoc_sync.doc_binding import resolve_declared_doc


class FakeLarkCLI:
    def __init__(self, node=None):
        self.node = node or {
            'obj_type': 'docx',
            'obj_token': 'docx_real_token',
        }

    def run_json(self, args):
        assert args[:4] == ['wiki', 'spaces', 'get_node', '--params']
        return {'node': self.node}


def test_resolve_docx_url_without_wiki_lookup():
    result = resolve_declared_doc(
        'https://example.feishu.cn/docx/AbCdEfGh',
        lark_cli=FakeLarkCLI(),
    )

    assert result.doc_key == 'docx:AbCdEfGh'
    assert result.resolved_doc_token == 'AbCdEfGh'


def test_resolve_wiki_url_via_lookup():
    result = resolve_declared_doc(
        'https://example.feishu.cn/wiki/WikiNodeToken',
        lark_cli=FakeLarkCLI(),
    )

    assert result.doc_key == 'docx:docx_real_token'
    assert result.resolved_file_type == 'docx'


def test_resolve_raw_token_defaults_to_docx():
    result = resolve_declared_doc('RawDocxToken', lark_cli=FakeLarkCLI())

    assert result.doc_key == 'docx:RawDocxToken'


def test_resolve_doc_key_cli_for_raw_token():
    result = subprocess.run(
        [sys.executable, 'scripts/resolve_doc_key.py', 'RawDocxToken'],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload['doc_key'] == 'docx:RawDocxToken'
```

- [ ] **Step 2: 运行测试，确认当前还没有绑定解析实现**

Run: `python3 -m pytest tests/test_doc_binding.py -q`
Expected: FAIL with import error for `doc_binding`

- [ ] **Step 3: 实现 `lark-cli` JSON 调用封装与绑定解析**

```python
# src/markdown_larkdoc_sync/lark_cli.py
from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Sequence
from typing import Any


class LarkCLIError(RuntimeError):
    pass


class LarkCLI:
    def __init__(self, binary: str | None = None):
        self.binary = binary or os.environ.get('MARKDOWN_LARKDOC_SYNC_LARK_CLI', 'lark-cli')

    def run_json(self, args: Sequence[str]) -> dict[str, Any]:
        result = subprocess.run(
            [self.binary, *args],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise LarkCLIError(result.stderr.strip() or result.stdout.strip())
        return json.loads(result.stdout)
```

```python
# src/markdown_larkdoc_sync/doc_binding.py
from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse

from markdown_larkdoc_sync.lark_cli import LarkCLI


@dataclass(frozen=True)
class ResolvedDoc:
    declared_doc: str
    resolved_doc_token: str
    resolved_file_type: str
    doc_key: str


def _extract_kind_and_token(declared_doc: str) -> tuple[str, str]:
    if '://' not in declared_doc:
        return 'docx', declared_doc

    parsed = urlparse(declared_doc)
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) >= 2 and parts[0] in {'docx', 'doc', 'wiki'}:
        return parts[0], parts[1]
    raise ValueError(f'unsupported declared doc: {declared_doc}')


def resolve_declared_doc(declared_doc: str, lark_cli: LarkCLI | None = None) -> ResolvedDoc:
    lark_cli = lark_cli or LarkCLI()
    kind, token = _extract_kind_and_token(declared_doc)

    if kind == 'wiki':
        node = lark_cli.run_json(['wiki', 'spaces', 'get_node', '--params', '{"token":"%s"}' % token])['node']
        kind = node['obj_type']
        token = node['obj_token']

    return ResolvedDoc(
        declared_doc=declared_doc,
        resolved_doc_token=token,
        resolved_file_type=kind,
        doc_key=f'{kind}:{token}',
    )


def to_payload(resolved: ResolvedDoc) -> dict[str, str]:
    return asdict(resolved)
```

```python
# scripts/resolve_doc_key.py
from __future__ import annotations

import argparse
import sys

from markdown_larkdoc_sync.doc_binding import resolve_declared_doc, to_payload
from markdown_larkdoc_sync.jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('declared_doc')
    args = parser.parse_args()
    dump_json(to_payload(resolve_declared_doc(args.declared_doc)), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 4: 运行绑定解析测试，确认解析与 CLI 合同通过**

Run: `python3 -m pytest tests/test_doc_binding.py -q`
Expected: PASS with `4 passed`

- [ ] **Step 5: 提交飞书绑定解析脚本**

```bash
git add src/markdown_larkdoc_sync/lark_cli.py src/markdown_larkdoc_sync/doc_binding.py scripts/resolve_doc_key.py tests/test_doc_binding.py
git commit -m 'feat: add lark document binding resolution script' -- src/markdown_larkdoc_sync/lark_cli.py src/markdown_larkdoc_sync/doc_binding.py scripts/resolve_doc_key.py tests/test_doc_binding.py
```

### Task 4: 实现 sync trailer 解析、基线发现与专用 commit 脚本

**Files:**
- Create: `src/markdown_larkdoc_sync/git_sync.py`
- Create: `scripts/find_last_sync_commit.py`
- Create: `scripts/create_sync_commit.py`
- Create: `tests/test_git_sync.py`

- [ ] **Step 1: 先写失败测试，覆盖 found、not_found、conflict 三种状态**

```python
# tests/test_git_sync.py
from markdown_larkdoc_sync.git_sync import build_sync_message, classify_candidates


def test_build_sync_message_contains_required_trailers():
    message = build_sync_message(
        markdown_path='docs/a.md',
        declared_doc='https://example.feishu.cn/wiki/x',
        identity='user',
        resolved_file_type='docx',
        resolved_doc_token='doc_real',
        profile='default',
    )

    assert 'Markdown-Larkdoc-Sync: success' in message
    assert 'Lark-Resolved-Doc-Token: doc_real' in message


def test_classify_candidates_returns_found():
    result = classify_candidates(
        [{'commit': 'abc', 'markdown_path': 'docs/a.md', 'doc_key': 'docx:doc_real'}],
        doc_key='docx:doc_real',
        markdown_path='docs/a.md',
        head_paths={'docs/a.md'},
    )

    assert result['status'] == 'found'
    assert result['commit'] == 'abc'


def test_classify_candidates_returns_conflict_for_live_old_path():
    result = classify_candidates(
        [{'commit': 'abc', 'markdown_path': 'docs/old.md', 'doc_key': 'docx:doc_real'}],
        doc_key='docx:doc_real',
        markdown_path='docs/new.md',
        head_paths={'docs/old.md', 'docs/new.md'},
    )

    assert result['status'] == 'conflict'
```

- [ ] **Step 2: 运行测试，确认 Git 同步工具尚未实现**

Run: `python3 -m pytest tests/test_git_sync.py -q`
Expected: FAIL with import error for `git_sync`

- [ ] **Step 3: 实现 trailer 构建、候选分类、基线发现与 commit 脚本**

```python
# src/markdown_larkdoc_sync/git_sync.py
from __future__ import annotations

import subprocess
from pathlib import Path


def build_sync_message(*, markdown_path: str, declared_doc: str, identity: str, resolved_file_type: str, resolved_doc_token: str, profile: str) -> str:
    return (
        f'sync(markdown-larkdoc): {markdown_path}\n\n'
        'Markdown-Larkdoc-Sync: success\n'
        f'Markdown-Path: {markdown_path}\n'
        f'Lark-Doc: {declared_doc}\n'
        f'Lark-Identity: {identity}\n'
        f'Lark-Resolved-Doc-Token: {resolved_doc_token}\n'
        f'Lark-Resolved-File-Type: {resolved_file_type}\n'
        f'Lark-Sync-Profile: {profile}\n'
    )


def classify_candidates(records: list[dict[str, str]], *, doc_key: str, markdown_path: str, head_paths: set[str]) -> dict[str, str]:
    matches = [record for record in records if record['doc_key'] == doc_key]
    if not matches:
        return {'status': 'not_found', 'doc_key': doc_key, 'commit': '', 'markdown_path': markdown_path, 'reason': 'no matching sync commit'}

    newest = matches[0]
    old_path = newest['markdown_path']
    if old_path and old_path != markdown_path and old_path in head_paths:
        return {'status': 'conflict', 'doc_key': doc_key, 'commit': newest['commit'], 'markdown_path': old_path, 'reason': 'old markdown path is still present in HEAD'}

    return {'status': 'found', 'doc_key': doc_key, 'commit': newest['commit'], 'markdown_path': old_path or markdown_path, 'reason': 'matched resolved doc trailers'}


def _parse_log_records(raw: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for chunk in raw.split('\x1e'):
        if not chunk.strip() or '\x1f' not in chunk:
            continue
        commit, body = chunk.split('\x1f', 1)
        trailers: dict[str, str] = {}
        for line in body.splitlines():
            if ': ' in line:
                key, value = line.split(': ', 1)
                trailers[key] = value
        if trailers.get('Markdown-Larkdoc-Sync') != 'success':
            continue
        file_type = trailers.get('Lark-Resolved-File-Type', '')
        doc_token = trailers.get('Lark-Resolved-Doc-Token', '')
        if not file_type or not doc_token:
            continue
        records.append({'commit': commit, 'markdown_path': trailers.get('Markdown-Path', ''), 'doc_key': f'{file_type}:{doc_token}'})
    return records


def _list_head_paths(repo_root: Path) -> set[str]:
    result = subprocess.run(['git', '-C', str(repo_root), 'ls-tree', '-r', '--name-only', 'HEAD'], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def find_last_sync_commit(repo_root: Path, doc_key: str, markdown_path: str) -> dict[str, str]:
    if not (repo_root / '.git').exists():
        return {'status': 'not_found', 'doc_key': doc_key, 'commit': '', 'markdown_path': markdown_path, 'reason': 'git repository not initialized'}
    result = subprocess.run(['git', '-C', str(repo_root), 'log', '--format=%H%x1f%B%x1e'], check=False, capture_output=True, text=True)
    records = _parse_log_records(result.stdout)
    return classify_candidates(records, doc_key=doc_key, markdown_path=markdown_path, head_paths=_list_head_paths(repo_root))
```

```python
# scripts/find_last_sync_commit.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdown_larkdoc_sync.git_sync import find_last_sync_commit
from markdown_larkdoc_sync.jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('doc_key')
    args = parser.parse_args()
    dump_json(find_last_sync_commit(Path.cwd(), args.doc_key, args.markdown_path), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

```python
# scripts/create_sync_commit.py
from __future__ import annotations

import argparse
import subprocess
import sys

from markdown_larkdoc_sync.git_sync import build_sync_message
from markdown_larkdoc_sync.jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('declared_doc')
    parser.add_argument('identity')
    parser.add_argument('resolved_file_type')
    parser.add_argument('resolved_doc_token')
    parser.add_argument('profile')
    args = parser.parse_args()

    subprocess.run(['git', 'add', args.markdown_path], check=True)
    subprocess.run(
        [
            'git',
            'commit',
            '-m',
            build_sync_message(
                markdown_path=args.markdown_path,
                declared_doc=args.declared_doc,
                identity=args.identity,
                resolved_file_type=args.resolved_file_type,
                resolved_doc_token=args.resolved_doc_token,
                profile=args.profile,
            ),
            '--',
            args.markdown_path,
        ],
        check=True,
    )
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    dump_json({'commit': commit}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 4: 运行 Git 同步工具测试，并补一个临时仓库 smoke test**

Run: `python3 -m pytest tests/test_git_sync.py -q`
Expected: PASS with `3 passed`

- [ ] **Step 5: 提交 Git 基线与 commit 脚本**

```bash
git add src/markdown_larkdoc_sync/git_sync.py scripts/find_last_sync_commit.py scripts/create_sync_commit.py tests/test_git_sync.py
git commit -m 'feat: add git sync baseline scripts' -- src/markdown_larkdoc_sync/git_sync.py scripts/find_last_sync_commit.py scripts/create_sync_commit.py tests/test_git_sync.py
```

### Task 5: 实现评论读取与批量 resolve 脚本

**Files:**
- Create: `src/markdown_larkdoc_sync/comments.py`
- Create: `scripts/fetch_open_comments.py`
- Create: `scripts/resolve_all_comments.py`
- Create: `tests/test_comments.py`

- [ ] **Step 1: 先写失败测试，覆盖评论拉平与 resolve payload 组装**

```python
# tests/test_comments.py
from markdown_larkdoc_sync.comments import build_resolve_payload, flatten_open_comments


def test_flatten_open_comments_skips_solved_cards():
    payload = {
        'items': [
            {'comment_id': 'c1', 'is_solved': False, 'reply_list': {'replies': [{'reply_id': 'r1'}]}},
            {'comment_id': 'c2', 'is_solved': True, 'reply_list': {'replies': [{'reply_id': 'r2'}]}},
        ]
    }

    items = flatten_open_comments(payload)
    assert [item['comment_id'] for item in items] == ['c1']


def test_build_resolve_payload_marks_comment_solved():
    payload = build_resolve_payload('doc_token', 'docx', 'c1')

    assert payload['params']['file_token'] == 'doc_token'
    assert payload['data']['file_type'] == 'docx'
    assert payload['data']['comment_id'] == 'c1'
    assert payload['data']['is_solved'] is True
```

- [ ] **Step 2: 运行测试，确认评论辅助模块尚未实现**

Run: `python3 -m pytest tests/test_comments.py -q`
Expected: FAIL with import error for `comments`

- [ ] **Step 3: 实现评论拉平、payload 生成与脚本接口**

```python
# src/markdown_larkdoc_sync/comments.py
from __future__ import annotations

import json


def flatten_open_comments(payload: dict) -> list[dict]:
    items = payload.get('items', [])
    return [item for item in items if not item.get('is_solved', False)]


def build_resolve_payload(file_token: str, file_type: str, comment_id: str) -> dict:
    return {
        'params': {'file_token': file_token},
        'data': {'file_type': file_type, 'comment_id': comment_id, 'is_solved': True},
    }


def dump_json_arg(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
```

```python
# scripts/fetch_open_comments.py
from __future__ import annotations

import argparse
import json
import sys

from markdown_larkdoc_sync.comments import flatten_open_comments
from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.lark_cli import LarkCLI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_token')
    args = parser.parse_args()

    raw = LarkCLI().run_json(['drive', 'file.comments', 'list', '--params', json.dumps({'file_token': args.file_token}, ensure_ascii=False)])
    dump_json({'items': flatten_open_comments(raw)}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

```python
# scripts/resolve_all_comments.py
from __future__ import annotations

import argparse
import sys

from markdown_larkdoc_sync.comments import build_resolve_payload, dump_json_arg
from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.lark_cli import LarkCLI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_token')
    parser.add_argument('file_type')
    parser.add_argument('comment_ids', nargs='+')
    args = parser.parse_args()

    lark = LarkCLI()
    results = []
    for comment_id in args.comment_ids:
        payload = build_resolve_payload(args.file_token, args.file_type, comment_id)
        results.append(
            lark.run_json(
                [
                    'drive',
                    'file.comments',
                    'patch',
                    '--params',
                    dump_json_arg(payload['params']),
                    '--data',
                    dump_json_arg(payload['data']),
                ]
            )
        )
    dump_json({'results': results}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 4: 运行评论脚本测试，确认核心逻辑通过**

Run: `python3 -m pytest tests/test_comments.py -q`
Expected: PASS with `2 passed`

- [ ] **Step 5: 在接入真实飞书前校验评论 patch schema**

Run: `lark-cli schema drive.file.comments.patch`
Expected: schema 输出中能看到 patch 请求体字段；如果字段名与 `build_resolve_payload()` 不一致，先修改实现与测试，再继续后续任务。

执行记录（2026-04-10，Asia/Shanghai）：
- 在仓库根目录执行 `lark-cli schema drive.file.comments.patch`，返回 `zsh:1: command not found: lark-cli`。
- 受限说明：当前环境不存在 `lark-cli` 可执行程序，无法直接完成 schema introspection。
- 替代校验：以 `tests/test_comments.py::test_build_resolve_payload_schema_field_contract` 锁定字段名 `file_token/file_type/comment_id/is_solved`。
- 补跑要求：环境恢复后重新执行该 schema 命令，并将输出追加到 `docs/superpowers/plans/task5-step5-schema-check-evidence.md`。

- [ ] **Step 6: 提交评论读取与 resolve 脚本**

```bash
git add src/markdown_larkdoc_sync/comments.py scripts/fetch_open_comments.py scripts/resolve_all_comments.py tests/test_comments.py
git commit -m 'feat: add lark comment helper scripts' -- src/markdown_larkdoc_sync/comments.py scripts/fetch_open_comments.py scripts/resolve_all_comments.py tests/test_comments.py
```

### Task 6: 实现运行 Journal 与失败恢复基础能力

**Files:**
- Create: `src/markdown_larkdoc_sync/journal.py`
- Create: `tests/test_journal.py`

- [ ] **Step 1: 先写失败测试，覆盖 `.git/markdown-larkdoc-sync/` 目录写入**

```python
# tests/test_journal.py
from markdown_larkdoc_sync.journal import Journal


def test_journal_writes_run_payload(tmp_path):
    git_dir = tmp_path / '.git'
    git_dir.mkdir()
    journal = Journal(git_dir)

    path = journal.write_run('run-1', {'phase': 'preflight'})

    assert path == git_dir / 'markdown-larkdoc-sync' / 'runs' / 'run-1.json'
    assert path.read_text(encoding='utf-8').strip().startswith('{')
```

- [ ] **Step 2: 运行测试，确认 journal 实现尚未存在**

Run: `python3 -m pytest tests/test_journal.py -q`
Expected: FAIL with import error for `journal`

- [ ] **Step 3: 实现最小 journal 写入器**

```python
# src/markdown_larkdoc_sync/journal.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Journal:
    def __init__(self, git_dir: Path):
        self.root = git_dir / 'markdown-larkdoc-sync'

    def write_run(self, run_id: str, payload: dict[str, Any]) -> Path:
        path = self.root / 'runs' / f'{run_id}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        return path
```

- [ ] **Step 4: 重新运行 journal 测试**

Run: `python3 -m pytest tests/test_journal.py -q`
Expected: PASS with `1 passed`

- [ ] **Step 5: 提交本地运行 journal 基础能力**

```bash
git add src/markdown_larkdoc_sync/journal.py tests/test_journal.py
git commit -m 'feat: add local sync journal helper' -- src/markdown_larkdoc_sync/journal.py tests/test_journal.py
```

### Task 7: 编写中文 skill 与 agents 元数据

**Files:**
- Create: `skills/markdown-larkdoc-sync/SKILL.md`
- Create: `skills/markdown-larkdoc-sync/agents/openai.yaml`
- Create: `tests/test_skill_docs.py`

- [ ] **Step 1: 先写失败测试，锁定 skill 中必须出现的中文约束与 sub-agent 审校要求**

```python
# tests/test_skill_docs.py
from pathlib import Path


def test_skill_mentions_single_v2_flow_and_subagent_review():
    content = Path('skills/markdown-larkdoc-sync/SKILL.md').read_text(encoding='utf-8')

    assert '只支持一个手动触发的 V2 工作流' in content
    assert '一致性审校必须由独立 sub-agent 执行' in content
    assert '成功收尾时要解决全部未解决评论' in content
```

- [ ] **Step 2: 运行测试，确认 skill 文档尚未存在**

Run: `python3 -m pytest tests/test_skill_docs.py -q`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: 编写中文 skill 与元数据文件**

```markdown
# skills/markdown-larkdoc-sync/SKILL.md
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
```

```yaml
# skills/markdown-larkdoc-sync/agents/openai.yaml
interface:
  display_name: 'Markdown LarkDoc Sync'
  short_description: '以中文执行单文档 Markdown 与飞书文档同步'
  default_prompt: '同步一篇 Markdown 与其绑定的飞书文档，遵循单一 V2 工作流与保守合并策略。'
```

- [ ] **Step 4: 运行 skill 文本合同测试**

Run: `python3 -m pytest tests/test_skill_docs.py -q`
Expected: PASS with `1 passed`

- [ ] **Step 5: 提交 skill 本体与元数据**

```bash
git add skills/markdown-larkdoc-sync/SKILL.md skills/markdown-larkdoc-sync/agents/openai.yaml tests/test_skill_docs.py
git commit -m 'feat: add markdown larkdoc sync skill' -- skills/markdown-larkdoc-sync/SKILL.md skills/markdown-larkdoc-sync/agents/openai.yaml tests/test_skill_docs.py
```

### Task 8: 收口测试矩阵并做端到端 smoke 计划

**Files:**
- Create: `tests/test_cli_smoke_contracts.py`
- Modify: `docs/superpowers/specs/2026-04-10-markdown-larkdoc-sync-design.md`
- Modify: `docs/superpowers/plans/2026-04-10-markdown-larkdoc-sync.md`

- [ ] **Step 1: 先写失败测试，锁定脚本输出字段完整性**

```python
# tests/test_cli_smoke_contracts.py
import json
import subprocess
import sys


def test_extract_markdown_body_contract(tmp_path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('# T\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, 'scripts/extract_markdown_body.py', str(markdown)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert sorted(payload.keys()) == ['body', 'frontmatter']
```

- [ ] **Step 2: 运行 smoke 合同测试，确认当前计划中的脚本尚未全部就绪**

Run: `python3 -m pytest tests/test_cli_smoke_contracts.py -q`
Expected: FAIL until all earlier tasks are complete

- [ ] **Step 3: 在所有前置任务完成后，补齐 smoke 测试并更新 spec/plan 的验证章节**

```text
在本任务中需要补充：
- `resolve_doc_key.py` 输出字段合同测试
- `find_last_sync_commit.py` 输出字段合同测试
- `create_sync_commit.py` 的临时仓库 smoke test
- `fetch_open_comments.py` 与 `resolve_all_comments.py` 的 fake lark-cli 注入测试
- 在 spec 与 plan 中补上最终验证命令集合
```

- [ ] **Step 4: 运行完整测试集，确认所有合同测试通过**

Run: `python3 -m pytest`
Expected: PASS with all tests green

- [ ] **Step 5: 提交测试矩阵与收口说明**

```bash
git add tests/test_cli_smoke_contracts.py docs/superpowers/specs/2026-04-10-markdown-larkdoc-sync-design.md docs/superpowers/plans/2026-04-10-markdown-larkdoc-sync.md
git commit -m 'test: add smoke contracts for sync scripts' -- tests/test_cli_smoke_contracts.py docs/superpowers/specs/2026-04-10-markdown-larkdoc-sync-design.md docs/superpowers/plans/2026-04-10-markdown-larkdoc-sync.md
```

## 最终验证命令集合（Task 8 收口）

Run: `python3 -m pytest tests/test_cli_smoke_contracts.py -q`
Expected: PASS with `6 passed`

Run: `python3 -m pytest tests/test_markdown_body.py tests/test_doc_binding.py tests/test_git_sync.py tests/test_comments.py -q`
Expected: PASS with all targeted module contracts green

Run: `python3 -m pytest`
Expected: PASS with all tests green

## 自检

- 规格覆盖：计划已覆盖 spec 中的 frontmatter 提取、`doc_key` 解析、`last_sync_commit` 脚本化、评论读取与 resolve、专用 sync commit、中文 skill、sub-agent 审校入口和 `.git` 下 journal。
- 占位符检查：计划中不使用 `TODO`、`TBD`、`implement later` 等占位语；唯一显式保留的执行门槛是 Task 5 中必须用真实 `lark-cli schema drive.file.comments.patch` 二次校验 patch 请求结构。
- 类型一致性：脚本统一以稳定 JSON 输出；`doc_key`、`markdown_path`、`resolved_doc_token`、`resolved_file_type` 等字段在所有任务中保持一致。
