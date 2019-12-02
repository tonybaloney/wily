import pathlib

from click.testing import CliRunner

import wily.__main__ as main


def test_list_metrics(builddir):
    """
    Test that list-metrics works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "list-metrics"])
    assert result.exit_code == 0, result.stdout


def test_clean(builddir):
    """ Test the clean feature """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "clean", "--yes"])
    assert result.exit_code == 0, result.stdout
    cache_path = pathlib.Path(builddir) / ".wily"
    assert not cache_path.exists()


def test_clean_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "clean"])
    assert result.exit_code == 0, result.stdout


def test_list_metrics_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "list-metrics"])
    assert result.exit_code == 1, result.stdout
