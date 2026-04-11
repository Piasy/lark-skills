import json
import subprocess
import sys
from pathlib import Path

from frontmatter import split_frontmatter


ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'bin'


def test_split_frontmatter_returns_mapping_and_body():
    frontmatter, body = split_frontmatter(
        '---\nmarkdown_larkdoc_sync:\n  doc: https://example/wiki/x\n  as: user\n  profile: default\n---\n\n# Title\n'
    )

    assert frontmatter['markdown_larkdoc_sync']['doc'].endswith('/x')
    assert body == '# Title\n'


def test_extract_markdown_body_cli_smoke(tmp_path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('---\ntitle: 示例\n---\n\n# Title\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(BIN / 'extract_markdown_body.py'), str(markdown)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    payload = json.loads(result.stdout)
    assert payload['frontmatter']['title'] == '示例'
    assert payload['body'] == '# Title\n'


def test_split_frontmatter_supports_crlf_boundaries():
    frontmatter, body = split_frontmatter('---\r\ntitle: CRLF\r\n---\r\n\r\n# Title\r\n')

    assert frontmatter == {'title': 'CRLF'}
    assert body == '# Title\r\n'


def test_split_frontmatter_allows_eof_after_closing_marker():
    frontmatter, body = split_frontmatter('---\ntitle: EOF\n---')

    assert frontmatter == {'title': 'EOF'}
    assert body == ''


def test_split_frontmatter_rejects_unknown_top_level_key():
    try:
        split_frontmatter('---\npublished: 2026-04-10\n---\n\n# Title\n')
    except ValueError as exc:
        assert 'unsupported top-level key' in str(exc)
    else:
        raise AssertionError('expected ValueError for unsupported top-level key')


def test_split_frontmatter_rejects_list_values():
    try:
        split_frontmatter('---\ntitle:\n- bad\n---\n\n# Title\n')
    except ValueError as exc:
        assert 'unsupported sequence style' in str(exc)
    else:
        raise AssertionError('expected ValueError for list-style frontmatter')
