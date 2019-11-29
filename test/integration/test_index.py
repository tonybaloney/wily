from click.testing import CliRunner

import wily.__main__ as main


def test_index_no_cache(tmpdir, cache_path):
    """
    Test that wily index fails in a directory that has no cache
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "--cache", cache_path, "index"])
    assert "An author" not in result.stdout
    assert result.exit_code == 1, result.stdout


def test_index(builddir):
    """
    Test that index works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "index"])
    assert result.stdout.count("An author") >= 3
    assert result.exit_code == 0, result.stdout


def test_index_with_messages(builddir):
    """
    Test that index works with a build with git commit messages
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "index", "--message"])
    assert result.stdout.count("An author") == 3
    assert "basic test" in result.stdout
    assert "add line" in result.stdout
    assert "remove line" in result.stdout
    assert result.exit_code == 0, result.stdout
