import json
import subprocess
import sys
from datetime import date, datetime, time

from markdown_larkdoc_sync.markdown_body import normalize_body, split_frontmatter
import markdown_larkdoc_sync.markdown_body as markdown_body


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


def test_extract_markdown_body_cli_converts_date_to_string(tmp_path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('---\npublished: 2026-04-10\n---\n\n# Title\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, 'scripts/extract_markdown_body.py', str(markdown)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload['frontmatter']['published'] == '2026-04-10'


def test_split_frontmatter_normalizes_yaml_temporal_values(monkeypatch):
    class FakeYaml:
        @staticmethod
        def safe_load(_: str):
            return {
                'published': date(2026, 4, 10),
                'nested': {
                    'updated': datetime(2026, 4, 10, 15, 45, 2),
                    'at': time(9, 30),
                    'tuple_values': (date(2026, 4, 11), time(8, 1)),
                    'set_values': {date(2026, 4, 12)},
                },
            }

    monkeypatch.setattr(markdown_body, 'yaml', FakeYaml)

    frontmatter, _ = split_frontmatter('---\nignored: true\n---\n\n# Title\n')

    assert frontmatter['published'] == '2026-04-10'
    assert frontmatter['nested']['updated'] == '2026-04-10T15:45:02'
    assert frontmatter['nested']['at'] == '09:30:00'
    assert frontmatter['nested']['tuple_values'] == ['2026-04-11', '08:01:00']
    assert frontmatter['nested']['set_values'] == ['2026-04-12']


def test_normalize_body_keeps_trailing_spaces_in_tilde_fence():
    body = '~~~\nline with spaces   \n~~~\n'

    assert normalize_body(body) == '~~~\nline with spaces   \n~~~\n'


def test_normalize_body_keeps_trailing_spaces_in_indented_backtick_fence():
    body = 'outside   \n\n  ```python\nline with spaces   \n  ```\n'

    assert normalize_body(body) == 'outside\n\n  ```python\nline with spaces   \n  ```\n'
