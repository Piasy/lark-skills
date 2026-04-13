from __future__ import annotations

import subprocess
from pathlib import Path


def resolve_repo_root(workdir: Path) -> Path:
    result = subprocess.run(
        ['git', '-C', str(workdir), 'rev-parse', '--show-toplevel'],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError('git repository not initialized')
    return Path(result.stdout.strip())


def to_repo_relative_markdown_path(markdown_path: str, *, repo_root: Path, cwd: Path | None = None) -> str:
    base_dir = cwd or Path.cwd()
    raw_path = Path(markdown_path)
    absolute = raw_path if raw_path.is_absolute() else (base_dir / raw_path)
    absolute = absolute.resolve()

    root = repo_root.resolve()
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise ValueError(f'markdown path is outside git repo root: {markdown_path}') from exc

    normalized = relative.as_posix()
    if not normalized or normalized == '.':
        raise ValueError(f'markdown path is not a file path: {markdown_path}')
    return normalized


def build_sync_message(
    *,
    markdown_path: str,
    declared_doc: str,
    identity: str,
    resolved_file_type: str,
    resolved_doc_token: str,
    profile: str,
) -> str:
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


def classify_candidates(
    records: list[dict[str, str]],
    *,
    doc_key: str,
    markdown_path: str,
    head_paths: set[str],
) -> dict[str, str]:
    matches = [record for record in records if record.get('doc_key') == doc_key]
    if not matches:
        return {
            'status': 'not_found',
            'doc_key': doc_key,
            'commit': '',
            'markdown_path': markdown_path,
            'reason': 'no matching sync commit',
        }

    newest = matches[0]
    old_path = newest.get('markdown_path', '')
    if old_path and old_path != markdown_path and old_path in head_paths:
        return {
            'status': 'conflict',
            'doc_key': doc_key,
            'commit': newest.get('commit', ''),
            'markdown_path': old_path,
            'reason': 'old markdown path is still present in HEAD',
        }

    return {
        'status': 'found',
        'doc_key': doc_key,
        'commit': newest.get('commit', ''),
        'markdown_path': old_path or markdown_path,
        'reason': 'matched resolved doc trailers',
    }


def _parse_log_records(raw: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for chunk in raw.split('\x1e'):
        block = chunk.strip()
        if not block or '\x1f' not in block:
            continue
        commit, body = block.split('\x1f', 1)
        trailers: dict[str, str] = {}
        for line in body.splitlines():
            if ': ' not in line:
                continue
            key, value = line.split(': ', 1)
            trailers[key] = value

        if trailers.get('Markdown-Larkdoc-Sync') != 'success':
            continue
        file_type = trailers.get('Lark-Resolved-File-Type', '')
        doc_token = trailers.get('Lark-Resolved-Doc-Token', '')
        if not file_type or not doc_token:
            continue

        records.append(
            {
                'commit': commit,
                'markdown_path': trailers.get('Markdown-Path', ''),
                'doc_key': f'{file_type}:{doc_token}',
            }
        )
    return records


def _list_head_paths(repo_root: Path) -> set[str]:
    result = subprocess.run(
        ['git', '-C', str(repo_root), 'ls-tree', '-r', '--name-only', 'HEAD'],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _is_git_repo(repo_root: Path) -> bool:
    result = subprocess.run(
        ['git', '-C', str(repo_root), 'rev-parse', '--is-inside-work-tree'],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == 'true'


def find_last_sync_commit(
    repo_root: Path,
    doc_key: str,
    markdown_path: str,
    *,
    cwd: Path | None = None,
) -> dict[str, str]:
    if not _is_git_repo(repo_root):
        return {
            'status': 'not_found',
            'doc_key': doc_key,
            'commit': '',
            'markdown_path': markdown_path,
            'reason': 'git repository not initialized',
        }

    try:
        normalized_markdown_path = to_repo_relative_markdown_path(
            markdown_path,
            repo_root=resolve_repo_root(repo_root),
            cwd=cwd or repo_root,
        )
    except (RuntimeError, ValueError) as exc:
        return {
            'status': 'not_found',
            'doc_key': doc_key,
            'commit': '',
            'markdown_path': markdown_path,
            'reason': str(exc),
        }

    result = subprocess.run(
        ['git', '-C', str(repo_root), 'log', '--format=%H%x1f%B%x1e'],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {
            'status': 'not_found',
            'doc_key': doc_key,
            'commit': '',
            'markdown_path': normalized_markdown_path,
            'reason': 'failed to read git log',
        }

    records = _parse_log_records(result.stdout)
    return classify_candidates(
        records,
        doc_key=doc_key,
        markdown_path=normalized_markdown_path,
        head_paths=_list_head_paths(repo_root),
    )
