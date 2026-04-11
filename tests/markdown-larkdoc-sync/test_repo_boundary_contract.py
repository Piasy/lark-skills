from pathlib import Path


def test_root_scripts_and_src_are_removed_after_migration():
    assert not Path('scripts').exists()
    assert not Path('src').exists()


def test_pyproject_has_no_pyyaml_runtime_dependency():
    content = Path('pyproject.toml').read_text(encoding='utf-8')
    assert 'PyYAML' not in content
