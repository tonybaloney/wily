import wily.__main__ as main
from mock import patch
from click.testing import CliRunner


def test_report_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "report", "src/test.py"])
        assert result.exit_code == 1, result.stdout


def test_report(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "src/test.py",
                "--metrics",
                "raw.multi,maintainability.rank",
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_granular(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "src/test.py:function1",
                "--metrics",
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
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "report", "src/test1.py", "--metrics", "raw.loc"],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" in result.stdout


def test_report_default_metrics(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "report", "src/test.py"])
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_with_message(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "src/test.py",
                "--metrics",
                "raw.multi",
                "--message",
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert "basic test" in result.stdout
        assert "remove line" in result.stdout
        assert "Not found" not in result.stdout


def test_report_high_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "report", "src/test.py", "--metrics", "raw.comments"],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_low_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "src/test.py",
                "--metrics",
                "maintainability.mi",
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout
