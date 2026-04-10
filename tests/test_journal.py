from pathlib import Path

from markdown_larkdoc_sync.journal import Journal


def test_write_run_persists_json_file_under_git_internal_dir(tmp_path: Path):
    git_dir = tmp_path / '.git'

    run_path = Journal(git_dir).write_run('run-1', {'phase': 'preflight'})

    expected_path = git_dir / 'markdown-larkdoc-sync' / 'runs' / 'run-1.json'
    assert run_path == expected_path
    assert run_path.exists()
    assert run_path.read_text(encoding='utf-8').startswith('{')
