import wily.__main__ as main
from mock import patch
from click.testing import CliRunner


def test_help():
    """
    Test that CLI when called with help options
    """
    with patch('wily.logger') as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ['--help', '--debug'])
        assert result.exit_code == 0


def test_build():
    """
    Test that build calls the build command
    """
    with patch('wily.commands.build.build') as build:
        runner = CliRunner()
        result = runner.invoke(main.cli, ['build'])
        assert result.exit_code == 0
        assert build.called_once


def test_build_with_opts():
    """
    Test that build calls the build command
    """
    with patch('wily.commands.build.build') as build:
        runner = CliRunner()
        result = runner.invoke(main.cli, ['build', '-h 1', '-o raw,maintainability'])
        assert result.exit_code == 0
        assert build.called_once
        assert build.call_args[1]['config'].max_revisions == 1
        assert build.call_args[1]['config'].operators == ['raw', 'maintainability']
