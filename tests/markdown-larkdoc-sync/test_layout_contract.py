from pathlib import Path


SKILL_ROOT = Path('skills/markdown-larkdoc-sync')


def test_runtime_layout_contains_required_bin_and_lib_files():
    expected = {
        'bin/resolve_doc_key.py',
        'bin/find_last_sync_commit.py',
        'bin/fetch_open_comments.py',
        'bin/fetch_remote_markdown.py',
        'bin/write_back_and_verify.py',
        'bin/create_bootstrap_doc.py',
        'bin/resolve_all_comments.py',
        'bin/create_sync_commit.py',
        'lib/__init__.py',
        'lib/jsonio.py',
        'lib/lark_cli.py',
        'lib/doc_binding.py',
        'lib/git_sync.py',
        'lib/comments.py',
        'lib/journal.py',
        'lib/mermaid_addons.py',
    }

    missing = [rel for rel in sorted(expected) if not (SKILL_ROOT / rel).exists()]
    assert missing == []
