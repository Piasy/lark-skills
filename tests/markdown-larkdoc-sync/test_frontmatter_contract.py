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
