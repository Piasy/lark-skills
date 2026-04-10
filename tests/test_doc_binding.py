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
        self.calls = []

    def run_json(self, args):
        assert args[:4] == ['wiki', 'spaces', 'get_node', '--params']
        self.calls.append(args)
        return {'node': self.node}


def test_resolve_docx_url_without_wiki_lookup():
    result = resolve_declared_doc(
        'https://example.feishu.cn/docx/AbCdEfGh',
        lark_cli=FakeLarkCLI(),
    )

    assert result.doc_key == 'docx:AbCdEfGh'
    assert result.resolved_doc_token == 'AbCdEfGh'


def test_resolve_wiki_url_via_lookup():
    lark_cli = FakeLarkCLI()
    result = resolve_declared_doc(
        'https://example.feishu.cn/wiki/WikiNodeToken',
        lark_cli=lark_cli,
    )

    assert json.loads(lark_cli.calls[0][4])['token'] == 'WikiNodeToken'
    assert result.doc_key == 'docx:docx_real_token'
    assert result.resolved_file_type == 'docx'


def test_resolve_raw_token_defaults_to_docx():
    result = resolve_declared_doc('RawDocxToken', lark_cli=FakeLarkCLI())

    assert result.doc_key == 'docx:RawDocxToken'


def test_resolve_scheme_less_url_rejected():
    try:
        resolve_declared_doc('example.feishu.cn/wiki/Token', lark_cli=FakeLarkCLI())
    except ValueError as exc:
        assert 'unsupported declared doc' in str(exc)
    else:
        raise AssertionError('expected ValueError for URL-like input without scheme')


def test_resolve_protocol_relative_url_rejected():
    try:
        resolve_declared_doc('//example.feishu.cn/wiki/Token', lark_cli=FakeLarkCLI())
    except ValueError as exc:
        assert 'unsupported declared doc' in str(exc)
    else:
        raise AssertionError('expected ValueError for protocol-relative URL-like input')


def test_resolve_path_like_declared_doc_rejected():
    try:
        resolve_declared_doc('wiki/Token', lark_cli=FakeLarkCLI())
    except ValueError as exc:
        assert 'unsupported declared doc' in str(exc)
    else:
        raise AssertionError('expected ValueError for path-like declared doc input')


def test_resolve_doc_key_cli_for_raw_token():
    result = subprocess.run(
        [sys.executable, 'scripts/resolve_doc_key.py', 'RawDocxToken'],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload['doc_key'] == 'docx:RawDocxToken'
