import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


def _run_script(script_name: str, args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout)


def _write_fake_lark_cli(tmp_path: Path) -> Path:
    log_path = tmp_path / 'fake-lark-cli.log'
    fake = tmp_path / 'fake-lark-cli.py'
    fake.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
log_path = os.environ.get('FAKE_LARK_LOG')
if log_path:
    with Path(log_path).open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(args, ensure_ascii=False) + '\\n')

if args[:3] == ['drive', 'file.comments', 'list']:
    print(json.dumps({'items': [
        {'comment_id': 'c1', 'is_solved': False},
        {'comment_id': 'c2', 'is_solved': True}
    ]}, ensure_ascii=False))
    raise SystemExit(0)

if args[:3] == ['drive', 'file.comments', 'patch']:
    params = json.loads(args[args.index('--params') + 1])
    data = json.loads(args[args.index('--data') + 1])
    print(json.dumps({'status': 'ok', 'params': params, 'data': data}, ensure_ascii=False))
    raise SystemExit(0)

print(json.dumps({'error': 'unsupported', 'args': args}, ensure_ascii=False), file=sys.stderr)
raise SystemExit(2)
""",
        encoding='utf-8',
    )
    fake.chmod(0o755)
    return fake


def test_extract_markdown_body_contract(tmp_path):
    markdown = tmp_path / 'doc.md'
    markdown.write_text('---\ntitle: smoke\n---\n\n# T\n', encoding='utf-8')

    payload = _run_script('extract_markdown_body.py', [str(markdown)], cwd=ROOT)

    assert sorted(payload.keys()) == ['body', 'frontmatter']
    assert payload['frontmatter'] == {'title': 'smoke'}
    assert payload['body'] == '# T\n'


def test_resolve_doc_key_contract_for_raw_token():
    payload = _run_script('resolve_doc_key.py', ['RawDocxToken'], cwd=ROOT)

    assert sorted(payload.keys()) == [
        'declared_doc',
        'doc_key',
        'resolved_doc_token',
        'resolved_file_type',
    ]
    assert payload['declared_doc'] == 'RawDocxToken'
    assert payload['resolved_file_type'] == 'docx'
    assert payload['resolved_doc_token'] == 'RawDocxToken'
    assert payload['doc_key'] == 'docx:RawDocxToken'


def test_find_last_sync_commit_contract_for_non_git_directory(tmp_path):
    payload = _run_script(
        'find_last_sync_commit.py',
        ['docs/a.md', 'docx:doc_real'],
        cwd=tmp_path,
    )

    assert sorted(payload.keys()) == ['commit', 'doc_key', 'markdown_path', 'reason', 'status']
    assert payload['status'] == 'not_found'
    assert payload['doc_key'] == 'docx:doc_real'
    assert payload['commit'] == ''
    assert payload['markdown_path'] == 'docs/a.md'
    assert isinstance(payload['reason'], str) and payload['reason']


def test_create_sync_commit_smoke_on_temp_repo(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()

    subprocess.run(['git', 'init'], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(['git', 'config', 'user.email', 'sync@example.com'], cwd=repo, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Sync Bot'], cwd=repo, check=True)

    doc = repo / 'docs' / 'a.md'
    doc.parent.mkdir(parents=True)
    doc.write_text('# Title\n', encoding='utf-8')
    subprocess.run(['git', 'add', 'docs/a.md'], cwd=repo, check=True)
    subprocess.run(['git', 'commit', '-m', 'init'], cwd=repo, check=True, capture_output=True, text=True)

    doc.write_text('# Title\n\nupdated\n', encoding='utf-8')

    payload = _run_script(
        'create_sync_commit.py',
        [
            'docs/a.md',
            'https://example.feishu.cn/wiki/x',
            'user',
            'docx',
            'doc_real',
            'default',
        ],
        cwd=repo,
    )

    assert list(payload.keys()) == ['commit']
    assert len(payload['commit']) == 40
    assert all(ch in '0123456789abcdef' for ch in payload['commit'])


def test_fetch_open_comments_with_fake_lark_cli_injection(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    log_path = tmp_path / 'fake-lark-cli.log'
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_LARK_LOG': str(log_path),
    }

    payload = _run_script('fetch_open_comments.py', ['doc_token'], cwd=ROOT, env=env)

    assert sorted(payload.keys()) == ['items']
    assert [item['comment_id'] for item in payload['items']] == ['c1']

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert calls[0][:3] == ['drive', 'file.comments', 'list']
    params = json.loads(calls[0][calls[0].index('--params') + 1])
    assert params == {'file_token': 'doc_token'}


def test_resolve_all_comments_with_fake_lark_cli_injection(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    log_path = tmp_path / 'fake-lark-cli.log'
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_LARK_LOG': str(log_path),
    }

    payload = _run_script(
        'resolve_all_comments.py',
        ['doc_token', 'docx', 'c1', 'c2'],
        cwd=ROOT,
        env=env,
    )

    assert sorted(payload.keys()) == ['results']
    assert len(payload['results']) == 2
    assert [item['data']['comment_id'] for item in payload['results']] == ['c1', 'c2']
    assert all(item['data']['is_solved'] is True for item in payload['results'])

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(calls) == 2
    assert all(call[:3] == ['drive', 'file.comments', 'patch'] for call in calls)
