from mock import patch

from click.testing import CliRunner

import wily.__main__ as main


PATCHED_ENV = {"BROWSER": "echo %s", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}


def test_rank_no_cache(tmpdir):
    """ Test the rank feature with no cache """
    runner = CliRunner()

    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", tmpdir, "rank", "src/test.py", "maintainability.mi"]
        )
    assert result.exit_code == 1, result.stdout


def test_rank_single_file_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a single file """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/test.py"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a directory """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/"])
    assert result.exit_code == 0, result.stdout


def test_rank_single_file_informational(builddir):
    """ Test the rank feature with Informational metric """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "rank", "src/test.py", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_custom_metric(builddir):
    """ Test the rank feature with AimHigh metric """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "rank", "src/", "raw.comments"]
        )
    assert result.exit_code == 0, result.stdout
