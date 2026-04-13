from pathlib import Path


def test_skill_mentions_frontmatter_and_script_contracts():
    content = Path('skills/markdown-larkdoc-sync/SKILL.md').read_text(encoding='utf-8')

    assert 'agent 不得手改 frontmatter' in content
    assert 'agent 不得自行解析 frontmatter' in content
    assert 'bin/read_frontmatter_binding.py' in content
    assert 'bin/write_frontmatter_binding.py' in content
    assert 'bin/write_back_and_verify.py' in content
    assert 'overwrite' in content
    assert 'bin/fetch_remote_markdown.py' in content
    assert 'bin/create_bootstrap_doc.py' in content
    assert '文本绘图 add-on' in content
    assert 'bin/resolve_all_comments.py' in content
