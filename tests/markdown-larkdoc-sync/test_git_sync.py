import json
import subprocess
import sys
from pathlib import Path

from git_sync import (
    build_sync_message,
    classify_candidates,
    find_last_sync_commit,
)


ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'skills' / 'markdown-larkdoc-sync' / 'bin'


def test_build_sync_message_contains_required_trailers():
    message = build_sync_message(
        markdown_path='docs/a.md',
        declared_doc='https://example.feishu.cn/wiki/x',
        identity='user',
        resolved_file_type='docx',
        resolved_doc_token='doc_real',
        profile='default',
    )

    assert message.startswith('sync(markdown-larkdoc): docs/a.md\n\n')
    assert 'Markdown-Larkdoc-Sync: success' in message
    assert 'Markdown-Path: docs/a.md' in message
    assert 'Lark-Resolved-Doc-Token: doc_real' in message


def test_classify_candidates_returns_found():
    result = classify_candidates(
        [{'commit': 'abc', 'markdown_path': 'docs/a.md', 'doc_key': 'docx:doc_real'}],
        doc_key='docx:doc_real',
        markdown_path='docs/a.md',
        head_paths={'docs/a.md'},
    )

    assert result['status'] == 'found'
    assert result['doc_key'] == 'docx:doc_real'
    assert result['commit'] == 'abc'


def test_classify_candidates_returns_conflict_for_live_old_path():
    result = classify_candidates(
        [{'commit': 'abc', 'markdown_path': 'docs/old.md', 'doc_key': 'docx:doc_real'}],
        doc_key='docx:doc_real',
        markdown_path='docs/new.md',
        head_paths={'docs/old.md', 'docs/new.md'},
    )

    assert result['status'] == 'conflict'
    assert result['markdown_path'] == 'docs/old.md'


def test_find_last_sync_commit_returns_not_found_for_non_git_repo(tmp_path):
    result = find_last_sync_commit(tmp_path, 'docx:doc_real', 'docs/a.md')

    assert result['status'] == 'not_found'
    assert result['doc_key'] == 'docx:doc_real'
    assert result['commit'] == ''
    assert result['markdown_path'] == 'docs/a.md'
    assert result['reason']


def test_git_sync_scripts_smoke_on_temp_repo(tmp_path):
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

    create_result = subprocess.run(
        [
            sys.executable,
            str(BIN / 'create_sync_commit.py'),
            'docs/a.md',
            'https://example.feishu.cn/wiki/x',
            'user',
            'docx',
            'doc_real',
            'default',
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    create_payload = json.loads(create_result.stdout)
    assert create_payload['commit']

    find_result = subprocess.run(
        [
            sys.executable,
            str(BIN / 'find_last_sync_commit.py'),
            'docs/a.md',
            'docx:doc_real',
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    find_payload = json.loads(find_result.stdout)

    assert find_payload['status'] == 'found'
    assert find_payload['doc_key'] == 'docx:doc_real'
    assert find_payload['markdown_path'] == 'docs/a.md'
    assert find_payload['commit'] == create_payload['commit']
