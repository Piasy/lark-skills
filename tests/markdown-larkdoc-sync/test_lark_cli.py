import pytest

from lark_cli import LarkCLI, LarkCLIError


def test_run_json_wraps_file_not_found_error(monkeypatch):
    def _raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError('missing binary')

    monkeypatch.setattr('lark_cli.subprocess.run', _raise_file_not_found)

    cli = LarkCLI(binary='missing-cli')
    with pytest.raises(LarkCLIError, match='missing binary'):
        cli.run_json(['whoami'])


def test_run_json_passes_cwd(monkeypatch):
    captured = {}

    class Result:
        returncode = 0
        stdout = '{}'
        stderr = ''

    def _fake_run(args, check, capture_output, text, cwd):
        captured['cwd'] = cwd
        captured['args'] = args
        return Result()

    monkeypatch.setattr('lark_cli.subprocess.run', _fake_run)

    cli = LarkCLI(binary='fake-cli')
    payload = cli.run_json(['whoami'], cwd='/tmp/work')

    assert payload == {}
    assert captured['cwd'] == '/tmp/work'
    assert captured['args'][:2] == ['fake-cli', 'whoami']


def test_list_profiles_from_auth_list(monkeypatch):
    class Result:
        returncode = 0
        stdout = (
            '[{"appId":"cli_a"}, {"appId":"cli_b"}, {"appId":"cli_a"}, {"tokenStatus":"valid"}]'
        )
        stderr = ''

    monkeypatch.setattr('lark_cli.subprocess.run', lambda *args, **kwargs: Result())

    cli = LarkCLI(binary='fake-cli')
    assert cli.list_profiles() == ['cli_a', 'cli_b']


def test_active_profile_parses_config_show(monkeypatch):
    class Result:
        returncode = 0
        stdout = 'Config file path: /tmp/fake/config.json\n{"profile":"cli_active"}\n'
        stderr = ''

    monkeypatch.setattr('lark_cli.subprocess.run', lambda *args, **kwargs: Result())

    cli = LarkCLI(binary='fake-cli')
    assert cli.active_profile() == 'cli_active'


def test_resolve_profile_prefers_requested_non_auto(monkeypatch):
    cli = LarkCLI(binary='fake-cli')
    monkeypatch.setattr(cli, 'active_profile', lambda: 'cli_active')
    monkeypatch.setattr(cli, 'list_profiles', lambda: ['cli_active'])

    assert cli.resolve_profile('requested_profile') == 'requested_profile'


def test_resolve_profile_uses_active_then_single(monkeypatch):
    cli = LarkCLI(binary='fake-cli')

    monkeypatch.setattr(cli, 'active_profile', lambda: 'cli_active')
    monkeypatch.setattr(cli, 'list_profiles', lambda: ['cli_other'])
    assert cli.resolve_profile(None) == 'cli_active'

    monkeypatch.setattr(cli, 'active_profile', lambda: None)
    monkeypatch.setattr(cli, 'list_profiles', lambda: ['only_one'])
    assert cli.resolve_profile('auto') == 'only_one'

    monkeypatch.setattr(cli, 'active_profile', lambda: None)
    monkeypatch.setattr(cli, 'list_profiles', lambda: ['p1', 'p2'])
    assert cli.resolve_profile(None) is None
