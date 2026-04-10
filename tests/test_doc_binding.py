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
