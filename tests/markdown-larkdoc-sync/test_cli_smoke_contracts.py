import json
import os
import subprocess
import sys
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'bin'


def _run_script(script_name: str, args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(
        [sys.executable, str(BIN / script_name), *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout)


def _write_fake_lark_cli(tmp_path: Path) -> Path:
    fake = tmp_path / 'fake-lark-cli.py'
    fake.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
import html
from pathlib import Path


def _extract_file_arg(value: str) -> str:
    if value.startswith('@'):
        return value[1:]
    return value


def _record(args):
    log_path = os.environ.get('FAKE_LARK_LOG')
    if log_path:
        with Path(log_path).open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(args, ensure_ascii=False) + '\\n')


args = sys.argv[1:]
_record(args)

if args[:2] == ['auth', 'list']:
    app_ids = os.environ.get('FAKE_LARK_APP_IDS', 'app_default').split(',')
    app_ids = [value.strip() for value in app_ids if value.strip()]
    payload = [
        {'appId': app_id, 'tokenStatus': 'valid', 'userName': 'Tester', 'userOpenId': f'ou_{index}'}
        for index, app_id in enumerate(app_ids, start=1)
    ]
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(0)

if args[:2] == ['config', 'show']:
    profile = os.environ.get('FAKE_LARK_ACTIVE_PROFILE', '').strip()
    if profile:
        print('Config file path: /tmp/fake-lark/config.json')
        print(json.dumps({'profile': profile}, ensure_ascii=False))
    else:
        print('Config file path: /tmp/fake-lark/config.json')
        print(json.dumps({'profile': ''}, ensure_ascii=False))
    raise SystemExit(0)

if args[:4] == ['wiki', 'spaces', 'get_node', '--params']:
    params = json.loads(args[4])
    token = params.get('token', '')
    print(json.dumps({'node': {'obj_type': 'docx', 'obj_token': f'resolved_{token}'}}, ensure_ascii=False))
    raise SystemExit(0)

if args[:3] == ['drive', 'file.comments', 'list']:
    params = json.loads(args[args.index('--params') + 1])
    if set(params.keys()) != {'file_token', 'file_type'}:
        print(json.dumps({'error': 'bad_params', 'params': params}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
    print(json.dumps({'items': [
        {'comment_id': 'c1', 'is_solved': False, 'reply_list': {'replies': [{'reply_id': 'r1'}]}},
        {'comment_id': 'c2', 'is_solved': True}
    ]}, ensure_ascii=False))
    raise SystemExit(0)

if args[:3] == ['drive', 'file.comments', 'patch']:
    params = json.loads(args[args.index('--params') + 1])
    data = json.loads(args[args.index('--data') + 1])
    if set(params.keys()) != {'file_token', 'comment_id', 'file_type'}:
        print(json.dumps({'error': 'bad_params', 'params': params}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
    if set(data.keys()) != {'is_solved'}:
        print(json.dumps({'error': 'bad_data', 'data': data}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
    print(json.dumps({'status': 'ok', 'params': params, 'data': data}, ensure_ascii=False))
    raise SystemExit(0)

if args[:2] == ['docs', '+create']:
    title = args[args.index('--title') + 1]
    identity = args[args.index('--as') + 1]
    markdown_arg = args[args.index('--markdown') + 1]
    markdown_path = _extract_file_arg(markdown_arg)
    markdown = Path(markdown_path).read_text(encoding='utf-8')

    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    create_doc_id = os.environ.get('FAKE_DOCS_CREATE_DOC_ID', 'created_doc')
    remote_file = remote_root / f'{create_doc_id}.md'

    if '```mermaid' in markdown:
        markdown = markdown.replace(
            '```mermaid\\nflowchart LR\\n  A --> B\\n```',
            '<whiteboard token="WB1" align="left"/>'
        )

    remote_file.write_text(markdown, encoding='utf-8')

    print(
        json.dumps(
            {
                'ok': True,
                'identity': identity,
                'data': {
                    'doc_id': create_doc_id,
                    'doc_url': f'https://example.feishu.cn/docx/{create_doc_id}',
                    'title': title,
                },
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)

if args[:2] == ['docs', '+update']:
    doc = args[args.index('--doc') + 1]
    mode = args[args.index('--mode') + 1]
    identity = args[args.index('--as') + 1]
    markdown_arg = args[args.index('--markdown') + 1]
    markdown_path = _extract_file_arg(markdown_arg)
    markdown = Path(markdown_path).read_text(encoding='utf-8')

    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    remote_file = remote_root / f'{doc}.md'
    remote_file.write_text(markdown, encoding='utf-8')

    print(
        json.dumps(
            {
                'ok': True,
                'tool': 'docs.update',
                'doc': doc,
                'mode': mode,
                'identity': identity,
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)

if args[:2] == ['docs', '+fetch']:
    doc = args[args.index('--doc') + 1]
    identity = args[args.index('--as') + 1]

    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    remote_file = remote_root / f'{doc}.md'
    markdown = remote_file.read_text(encoding='utf-8') if remote_file.exists() else ''

    if os.environ.get('FAKE_DOCS_FETCH_APPEND_NEWLINE') == '1':
        markdown = markdown + '\\n'
    if os.environ.get('FAKE_DOCS_FETCH_FORCE_SUFFIX'):
        markdown = markdown + os.environ['FAKE_DOCS_FETCH_FORCE_SUFFIX']

    print(
        json.dumps(
            {
                'ok': True,
                'identity': identity,
                'data': {'markdown': markdown},
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0)

if args[:2] == ['api', 'GET'] and args[2].startswith('/open-apis/docx/v1/documents/') and args[2].endswith('/blocks'):
    path = args[2]
    doc_id = path.split('/')[5]
    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    remote_file = remote_root / f'{doc_id}.md'
    markdown = remote_file.read_text(encoding='utf-8') if remote_file.exists() else ''

    lines = markdown.splitlines()
    items = [
        {
            'block_id': doc_id,
            'block_type': 1,
            'children': [f'p_{i}' for i in range(len(lines))],
            'page': {'elements': []},
            'parent_id': '',
        }
    ]

    for i, line in enumerate(lines):
        items.append(
            {
                'block_id': f'p_{i}',
                'block_type': 2,
                'parent_id': doc_id,
                'text': {
                    'elements': [
                        {
                            'text_run': {
                                'content': line,
                                'text_element_style': {
                                    'bold': False,
                                    'italic': False,
                                    'strikethrough': False,
                                    'underline': False,
                                    'inline_code': False,
                                },
                            }
                        }
                    ]
                },
            }
        )

    print(json.dumps({'code': 0, 'data': {'items': items, 'has_more': False}, 'msg': 'success'}, ensure_ascii=False))
    raise SystemExit(0)


if args[:2] == ['api', 'DELETE'] and '/children/batch_delete' in args[2]:
    path = args[2]
    doc_id = path.split('/')[5]
    data = json.loads(args[args.index('--data') + 1])
    start = data['start_index']
    end = data['end_index']

    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    remote_file = remote_root / f'{doc_id}.md'
    lines = remote_file.read_text(encoding='utf-8').splitlines()

    lines = [line for i, line in enumerate(lines) if i < start or i >= end]
    remote_file.write_text('\\n'.join(lines) + ('\\n' if lines else ''), encoding='utf-8')

    print(json.dumps({'code': 0, 'data': {'start_index': start, 'end_index': end}, 'msg': 'success'}, ensure_ascii=False))
    raise SystemExit(0)


if args[:2] == ['api', 'POST'] and '/children' in args[2]:
    path = args[2]
    doc_id = path.split('/')[5]
    data = json.loads(args[args.index('--data') + 1])

    child = data['children'][0]
    record = child['add_ons']['record']
    escaped_record = html.escape(record, quote=True)
    addon_line = (
        '<add-ons component-id="" component-type-id="blk_631fefbbae02400430b8f9f4" '
        f'record="{escaped_record}"/>'
    )

    remote_root = Path(os.environ['FAKE_DOCS_REMOTE_ROOT'])
    remote_file = remote_root / f'{doc_id}.md'
    lines = remote_file.read_text(encoding='utf-8').splitlines()

    index = data.get('index', len(lines))
    if index < 0 or index > len(lines):
        index = len(lines)
    lines.insert(index, addon_line)

    remote_file.write_text('\\n'.join(lines) + ('\\n' if lines else ''), encoding='utf-8')

    print(json.dumps({'code': 0, 'data': {'index': index}, 'msg': 'success'}, ensure_ascii=False))
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

    payload = _run_script('fetch_open_comments.py', ['doc_token', 'docx'], cwd=ROOT, env=env)

    assert sorted(payload.keys()) == ['items']
    assert [item['comment_id'] for item in payload['items']] == ['c1']
    assert payload['items'][0]['reply_list']['replies'][0]['reply_id'] == 'r1'

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert calls[0][:3] == ['drive', 'file.comments', 'list']
    params = json.loads(calls[0][calls[0].index('--params') + 1])
    assert params == {'file_token': 'doc_token', 'file_type': 'docx'}


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
        ['doc_token', 'docx'],
        cwd=ROOT,
        env=env,
    )

    assert sorted(payload.keys()) == ['resolved_comment_ids', 'results']
    assert payload['resolved_comment_ids'] == ['c1']
    assert len(payload['results']) == 1
    assert [item['params']['comment_id'] for item in payload['results']] == ['c1']
    assert all(item['params']['file_type'] == 'docx' for item in payload['results'])
    assert all(item['data']['is_solved'] is True for item in payload['results'])

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(calls) == 2
    assert calls[0][:3] == ['drive', 'file.comments', 'list']
    assert calls[1][:3] == ['drive', 'file.comments', 'patch']


def test_write_back_and_verify_contract_with_fake_lark_cli(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    log_path = tmp_path / 'fake-lark-cli.log'
    remote_root = tmp_path / 'remote-docs'
    remote_root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_LARK_LOG': str(log_path),
        'FAKE_DOCS_REMOTE_ROOT': str(remote_root),
    }

    markdown = tmp_path / 'doc.md'
    markdown.write_text(
        '---\n'
        'title: Smoke\n'
        'markdown_larkdoc_sync:\n'
        '  doc: doc_token\n'
        '  as: user\n'
        '  profile: default\n'
        '---\n\n'
        '## Body\n\n'
        '```mermaid\n'
        'flowchart LR\n'
        '  A --> B\n'
        '```\n',
        encoding='utf-8',
    )

    payload = _run_script(
        'write_back_and_verify.py',
        [str(markdown), 'doc_token', 'user'],
        cwd=ROOT,
        env=env,
    )

    assert payload['mode'] == 'overwrite'
    assert payload['verified'] is True
    assert payload['identity'] == 'user'
    assert payload['declared_doc'] == 'doc_token'
    assert payload['remote_addons_converted'] == 1
    assert payload['mermaid_block_count'] == 1
    assert len(payload['addon_replacements']) == 1

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert calls[0][:2] == ['docs', '+update']
    assert calls[1][:2] == ['api', 'GET']
    assert calls[2][:2] == ['api', 'DELETE']
    assert calls[3][:2] == ['api', 'POST']
    assert calls[4][:2] == ['docs', '+fetch']
    assert '--mode' in calls[0]
    assert calls[0][calls[0].index('--mode') + 1] == 'overwrite'


def test_write_back_and_verify_returns_non_zero_on_mismatch(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    remote_root = tmp_path / 'remote-docs'
    remote_root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_DOCS_REMOTE_ROOT': str(remote_root),
        'FAKE_DOCS_FETCH_FORCE_SUFFIX': '[[mismatch]]',
    }

    markdown = tmp_path / 'doc.md'
    markdown.write_text(
        '---\n'
        'title: Smoke\n'
        'markdown_larkdoc_sync:\n'
        '  doc: doc_token\n'
        '  as: user\n'
        '  profile: default\n'
        '---\n\n'
        '## Body\n\n'
        'content',
        encoding='utf-8',
    )

    result = subprocess.run(
        [sys.executable, str(BIN / 'write_back_and_verify.py'), str(markdown), 'doc_token', 'user'],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload['verified'] is False
    assert payload['reason'] == 'remote canonical body differs from local canonical body after overwrite/add-on write-back'


def test_fetch_remote_markdown_can_return_canonical_content(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    remote_root = tmp_path / 'remote-docs'
    remote_root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_DOCS_REMOTE_ROOT': str(remote_root),
    }

    remote_file = remote_root / 'doc_token.md'
    remote_file.write_text(
        '<add-ons component-id="" component-type-id="blk_631fefbbae02400430b8f9f4" '
        'record="{&quot;data&quot;:&quot;flowchart LR\\n  A --&gt; B&quot;,&quot;theme&quot;:&quot;default&quot;,&quot;view&quot;:&quot;codeChart&quot;}"/>\n',
        encoding='utf-8',
    )

    payload = _run_script(
        'fetch_remote_markdown.py',
        ['doc_token', 'user', '--canonical'],
        cwd=ROOT,
        env=env,
    )

    assert payload['addon_mermaid_converted'] == 1
    assert payload['contains_whiteboard'] is False
    assert payload['resolved_doc_token'] == 'doc_token'
    assert payload['markdown'].startswith('```mermaid\n')


def test_create_bootstrap_doc_contract_with_fake_lark_cli(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    remote_root = tmp_path / 'remote-docs'
    remote_root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_DOCS_REMOTE_ROOT': str(remote_root),
        'FAKE_DOCS_CREATE_DOC_ID': 'boot_doc_1',
        'FAKE_LARK_APP_IDS': 'app_default',
        'FAKE_LARK_ACTIVE_PROFILE': 'app_default',
    }

    markdown = tmp_path / 'bootstrap.md'
    markdown.write_text(
        '# Boot\n\n'
        '```mermaid\n'
        'flowchart LR\n'
        '  A --> B\n'
        '```\n',
        encoding='utf-8',
    )

    payload = _run_script(
        'create_bootstrap_doc.py',
        [str(markdown), '--title', 'Bootstrap Title', '--identity', 'user'],
        cwd=ROOT,
        env=env,
    )

    assert payload['doc_id'] == 'boot_doc_1'
    assert payload['auto_normalized'] is True
    assert payload['normalized_verified'] is True
    assert payload['effective_profile'] == 'app_default'
    assert payload['profile_resolution'] in {'active_profile', 'single_profile'}
    assert payload['contains_whiteboard'] is False
    assert payload['mode'] == 'overwrite'
    assert payload['remote_addons_converted'] == 1
    assert payload['mermaid_block_count'] == 1
    assert len(payload['addon_replacements']) == 1
    assert 'auto-runs overwrite + mermaid add-on rewrite' in payload['bootstrap_warning']


def test_create_bootstrap_doc_falls_back_when_requested_profile_missing(tmp_path):
    fake_lark = _write_fake_lark_cli(tmp_path)
    log_path = tmp_path / 'fake-lark-cli.log'
    remote_root = tmp_path / 'remote-docs'
    remote_root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        'MARKDOWN_LARKDOC_SYNC_LARK_CLI': str(fake_lark),
        'FAKE_LARK_LOG': str(log_path),
        'FAKE_DOCS_REMOTE_ROOT': str(remote_root),
        'FAKE_DOCS_CREATE_DOC_ID': 'boot_doc_2',
        'FAKE_LARK_APP_IDS': 'cli_real_1',
        'FAKE_LARK_ACTIVE_PROFILE': 'cli_real_1',
    }

    markdown = tmp_path / 'bootstrap.md'
    markdown.write_text('# Boot\n', encoding='utf-8')

    payload = _run_script(
        'create_bootstrap_doc.py',
        [str(markdown), '--title', 'Bootstrap Title', '--identity', 'user', '--profile', 'default'],
        cwd=ROOT,
        env=env,
    )

    assert payload['doc_id'] == 'boot_doc_2'
    assert payload['requested_profile'] == 'default'
    assert payload['effective_profile'] == 'cli_real_1'
    assert payload['profile_resolution'] in {'fallback_active_profile', 'fallback_single_profile'}
    assert 'profile_warning' in payload

    calls = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    create_call = next(call for call in calls if call[:2] == ['docs', '+create'])
    assert '--profile' in create_call
    assert create_call[create_call.index('--profile') + 1] == 'cli_real_1'
