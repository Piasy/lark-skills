from pathlib import Path


def _has_non_cache_files(path: Path) -> bool:
    if not path.exists():
        return False

    for child in path.rglob('*'):
        if child.is_dir():
            if child.name == '__pycache__':
                continue
            continue
        if '__pycache__' in child.parts:
            continue
        return True

    return False


def test_root_scripts_and_src_have_no_runtime_sources_after_migration():
    assert not _has_non_cache_files(Path('scripts'))
    assert not _has_non_cache_files(Path('src'))


def test_pyproject_has_no_pyyaml_runtime_dependency():
    content = Path('pyproject.toml').read_text(encoding='utf-8')
    assert 'PyYAML' not in content
