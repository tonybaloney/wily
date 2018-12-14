from click.testing import CliRunner

import wily.__main__ as main


def test_report_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "report", "src/test.py"])
    assert result.exit_code == 1, result.stdout


def test_report(builddir):
    """
    Test that report works with a build and a specific metric
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--path",
            builddir,
            "report",
            "src/test.py",
            "raw.multi",
            "maintainability.rank",
        ],
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
            "src/test.py:function1",
            "cyclomatic.complexity",
            "-n",
            1,
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_not_found(builddir):
    """
    Test that report works with a build but not with an invalid path
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", "src/test1.py", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" in result.stdout


def test_report_default_metrics(builddir):
    """
    Test that report works with default metrics
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "report", "src/test.py"])
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
        main.cli,
        ["--path", builddir, "report", "src/test.py", "raw.multi", "--message"],
    )
    assert result.exit_code == 0, result.stdout
    assert "basic test" in result.stdout
    assert "remove line" in result.stdout
    assert "Not found" not in result.stdout


def test_report_high_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", "src/test.py", "raw.comments"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout


def test_report_low_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "report", "src/test.py", "maintainability.mi"]
    )
    assert result.exit_code == 0, result.stdout
    assert "Not found" not in result.stdout
