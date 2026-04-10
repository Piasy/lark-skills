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


def test_split_frontmatter_supports_crlf_boundaries():
    frontmatter, body = split_frontmatter('---\r\ntitle: CRLF\r\n---\r\n\r\n# Title\r\n')

    assert frontmatter == {'title': 'CRLF'}
    assert body == '# Title\r\n'


def test_split_frontmatter_allows_eof_after_closing_marker():
    frontmatter, body = split_frontmatter('---\ntitle: EOF\n---')

    assert frontmatter == {'title': 'EOF'}
    assert body == ''
