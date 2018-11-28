from click.testing import CliRunner

import wily.__main__ as main


def test_index_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "index"])
    assert result.exit_code == 1, result.stdout


def test_index(builddir):
    """
    Test that index works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "index"])
    assert result.exit_code == 0, result.stdout


def test_index_with_messages(builddir):
    """
    Test that index works with a build with git commit messages
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "index", "--message"])
    assert result.exit_code == 0, result.stdout
