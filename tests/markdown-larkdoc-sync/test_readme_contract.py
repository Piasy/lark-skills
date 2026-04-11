from pathlib import Path


def test_readme_zh_contains_install_and_scope_statements():
    content = Path('README.zh.md').read_text(encoding='utf-8')
    assert 'skills source repository' in content
    assert 'Piasy/lark-skills' in content
    assert 'npx skills add Piasy/lark-skills -g -y' in content
    assert '不需要先手动 clone' in content
    assert 'frontmatter 是受限子集' in content
    assert 'MIT' in content


def test_readme_en_contains_install_and_scope_statements():
    content = Path('README.md').read_text(encoding='utf-8')
    assert 'skills source repository' in content
    assert 'npx skills add Piasy/lark-skills -g -y' in content
    assert 'frontmatter' in content
    assert 'MIT License' in content


def test_mit_license_exists():
    assert 'MIT License' in Path('LICENSE').read_text(encoding='utf-8')
