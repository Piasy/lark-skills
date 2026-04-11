import pytest

from lark_cli import LarkCLI, LarkCLIError


def test_run_json_wraps_file_not_found_error(monkeypatch):
    def _raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError('missing binary')

    monkeypatch.setattr('lark_cli.subprocess.run', _raise_file_not_found)

    cli = LarkCLI(binary='missing-cli')
    with pytest.raises(LarkCLIError, match='missing binary'):
        cli.run_json(['whoami'])
