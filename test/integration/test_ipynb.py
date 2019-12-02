import sys
from click.testing import CliRunner

import wily.__main__ as main

_path = "src\\test.ipynb" if sys.platform == "win32" else "src/test.ipynb"


def test_index_with_ipynb(ipynbbuilddir):
    """
    Test that index works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", ipynbbuilddir, "index"])
    assert result.stdout.count("An author") >= 3
    assert result.exit_code == 0, result.stdout


def test_index_and_message_with_ipynb(ipynbbuilddir):
    """
    Test that index works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", ipynbbuilddir, "index", "--message"])
    assert result.stdout.count("An author") >= 3
    assert "empty notebook" in result.stdout
    assert "single cell" in result.stdout
    assert "second cell" in result.stdout
    assert result.exit_code == 0, result.stdout


def test_report(ipynbbuilddir):
    """
    Test that report works with a build and a specific metric
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", ipynbbuilddir, "report", _path, "raw.multi", "maintainability.rank"],
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout
