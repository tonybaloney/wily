import sys

from click.testing import CliRunner
from pathlib import Path

import wily.__main__ as main

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"


def test_report_no_cache(tmpdir, cache_path):
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", tmpdir, "--cache", cache_path, "report", _path]
    )
    assert result.exit_code == 1, result.stdout


def test_report(builddir):
    """
    Test that report works with a build and a specific metric
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "report", _path, "raw.multi", "maintainability.rank"],
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_granular(builddir):
    """
    Test that report works with a build against specific metrics and a function
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--path",
            builddir,
            "report",
            _path + ":function1",
            "cyclomatic.complexity",
            "--message",
            "-n",
            1,
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "remove line" in result.stdout


def test_report_not_found(builddir):
    """
    Test that report works with a build but not with an invalid path
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", "test1.py", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" in result.stdout


def test_report_default_metrics(builddir):
    """
    Test that report works with default metrics
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "report", _path])
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_path(builddir):
    """
    Test that report with a path to a folder (aggregate values)
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "report", "src"])
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_with_message(builddir):
    """
    Test that report works messages in UI
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "raw.multi", "--message"]
    )
    assert result.exit_code == 0, result.stdout
    assert "basic test" in result.stdout
    assert "remove line" in result.stdout
    assert "Not found" not in result.stdout


def test_report_with_message_and_n(builddir):
    """
    Test that report works messages in UI
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "report", _path, "raw.multi", "--message", "-n", 1],
    )
    assert result.exit_code == 0, result.stdout
    assert "basic test" not in result.stdout
    assert "remove line" in result.stdout
    assert "Not found" not in result.stdout


def test_report_high_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "raw.comments"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_short_metric(builddir):
    """
    Test that report works with a build on shorthand metric
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "report", _path, "sloc"])
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_low_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "maintainability.mi"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_html_format(builddir):
    """
    Test that report works with HTML as format
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "--format", "HTML"]
    )
    path = Path().cwd()
    path = path / "wily_report" / "index.html"

    assert path.exists()
    assert "<html>" in path.read_text()
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_html_format_target_folder(builddir):
    """
    Test that report works with HTML as format
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "--format", "HTML", "-o", "foo"]
    )
    path = Path().cwd()
    path = path / "foo" / "index.html"

    assert path.exists()
    assert "<html>" in path.read_text()
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_html_format_target_file(builddir):
    """
    Test that report works with HTML as format
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "report", _path, "--format", "HTML", "-o", "foo/bar.html"],
    )
    path = Path().cwd()
    path = path / "foo" / "bar.html"

    assert path.exists()
    assert "<html>" in path.read_text()
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_console_format(builddir):
    """
    Test that report works with console as format
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "--format", "CONSOLE"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_not_existing_format(builddir):
    """
    Test that report works with non-existing format
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", _path, "--format", "non-existing"]
    )
    assert result.exit_code == 2, result.stdout
    assert "Not found" not in result.stdout
