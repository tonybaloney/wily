from click.testing import CliRunner

import wily.__main__ as main


def test_rank_no_cache(tmpdir):
    """ Test the rank feature with no cache """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "rank", "src/test.py"])
    assert result.exit_code == 1, result.stdout


def test_rank_single_file_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a single file """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/test.py"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a directory """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/"])
    assert result.exit_code == 0, result.stdout


def test_rank_single_file_informational(builddir):
    """ Test the rank feature with Informational metric """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/test.py", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_custom_metric(builddir):
    """ Test the rank feature with AimHigh metric """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_limit(builddir):
    """ Test the rank feature with limit """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "-l 2"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_desc(builddir):
    """ Test the rank feature descending order """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--desc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_asc(builddir):
    """ Test the rank feature ascending order"""
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--asc"]
    )
    assert result.exit_code == 0, result.stdout
