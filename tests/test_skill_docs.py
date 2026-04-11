from pathlib import Path


def test_skill_mentions_frontmatter_and_script_contracts():
    content = Path('skills/markdown-larkdoc-sync/SKILL.md').read_text(encoding='utf-8')

    assert 'agent 不得手改 frontmatter' in content
    assert 'agent 不得自行解析 frontmatter' in content
    assert 'bin/read_frontmatter_binding.py' in content
    assert 'bin/write_frontmatter_binding.py' in content
    assert 'bin/resolve_all_comments.py' in content
