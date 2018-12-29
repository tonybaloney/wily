import pytest

from click.testing import CliRunner
from mock import patch
from pathlib import Path

import wily.__main__ as main

from wily.helper.custom_enums import ReportFormat


def test_init():
    with patch.object(main, "cli", return_value=None) as cli:
        with patch.object(main, "__name__", "__main__"):
            __import__("wily.__main__")
            assert cli.called_once


def test_help():
    """
    Test that CLI when called with help options
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--help", "--debug"])
        assert result.exit_code == 0


def test_setup():
    """
    Test that CLI when called with help options
    """
    with patch("wily.__main__.handle_no_cache", return_value=True) as handle_no_cache:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup"])
        assert result.exit_code == 0
        assert handle_no_cache.called_once


def test_handle_no_cache_no():
    """
    Test that setup cancels when "n" typed
    """
    with patch("wily.__main__.input", return_value="n") as mock_input:
        with pytest.raises(SystemExit):
            main.handle_no_cache(None)
            assert mock_input.called_once


def test_handle_no_cache():
    """
    Test that setup works
    """
    with patch("wily.__main__.build", return_value="n") as build_command:
        with patch("wily.__main__.input", side_effect=["y", "11", "."]) as mock_input:
            runner = CliRunner()
            runner.invoke(main.cli, ["setup"])
            assert mock_input.called
            assert build_command.called_once
            assert build_command.called_with("1")


def test_build():
    """
    Test that build calls the build command
    """
    with patch("wily.commands.build.build") as build:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["build", "wily"])
        assert result.exit_code == 0
        assert build.called_once


def test_build_with_opts():
    """
    Test that build calls the build command
    """
    with patch("wily.commands.build.build") as build:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["build", "wily", "-n 1", "-o raw,maintainability"]
        )
        assert result.exit_code == 0
        assert build.called_once
        assert build.call_args[1]["config"].max_revisions == 1
        assert build.call_args[1]["config"].operators == ["raw", "maintainability"]


def test_index():
    """
    Test that index calls the index command
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.index.index") as index:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["index"])
            assert result.exit_code == 0
            assert index.called_once
            assert check_cache.called_once


def test_index_with_opts():
    """
    Test that index calls the index command with options
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.index.index") as index:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["index", "--message"])
            assert result.exit_code == 0
            assert index.called_once
            assert check_cache.called_once
            assert index.call_args[1]["include_message"]


def test_index_with_no_message():
    """
    Test that index calls the index command with options
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.index.index") as index:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["index", "--no-message"])
            assert result.exit_code == 0
            assert index.called_once
            assert check_cache.called_once
            assert not index.call_args[1]["include_message"]


def test_report():
    """
    Test that report calls the report command
    """
    with patch(
        "wily.__main__.get_default_metrics",
        return_value=["maintainability.mi", "raw.loc"],
    ) as gdf:
        with patch("wily.__main__.exists", return_value=True) as check_cache:
            with patch("wily.commands.report.report") as report:
                runner = CliRunner()
                result = runner.invoke(main.cli, ["report", "foo.py"])
                assert result.exit_code == 0, result.stdout
                assert report.called_once
                assert check_cache.called_once
                assert report.call_args[1]["path"] == "foo.py"
                assert report.call_args[1]["format"] == ReportFormat.CONSOLE
                assert "maintainability.mi" in report.call_args[1]["metrics"]
                assert gdf.called_once


def test_report_with_opts():
    """
    Test that report calls the report command with options
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(
                main.cli, ["report", "foo.py", "example_metric", "-n 101", "--message"]
            )
            assert result.exit_code == 0, result.stdout
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metrics"] == ("example_metric",)
            assert report.call_args[1]["include_message"]
            assert report.call_args[1]["n"] == 101
            assert report.call_args[1]["format"] == ReportFormat.CONSOLE


def test_report_html_format():
    """
    Test that report calls the report command with HTML as format
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(
                main.cli,
                [
                    "report",
                    "foo.py",
                    "example_metric",
                    "-n 101",
                    "--message",
                    "--format=HTML",
                ],
            )

            assert result.exit_code == 0, result.stdout
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metrics"] == ("example_metric",)
            assert report.call_args[1]["include_message"]
            assert report.call_args[1]["n"] == 101
            assert report.call_args[1]["format"] == ReportFormat.HTML


def test_report_console_format():
    """
    Test that report calls the report command with console as format
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(
                main.cli,
                [
                    "report",
                    "foo.py",
                    "example_metric",
                    "-n 101",
                    "--message",
                    "--format=CONSOLE",
                ],
            )
            assert result.exit_code == 0, result.stdout
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metrics"] == ("example_metric",)
            assert report.call_args[1]["include_message"]
            assert report.call_args[1]["n"] == 101
            assert report.call_args[1]["format"] == ReportFormat.CONSOLE


def test_report_not_existing_format():
    """
    Test that report calls the report command with a non-existing format
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(
                main.cli,
                [
                    "report",
                    "foo.py",
                    "example_metric",
                    "-n 101",
                    "--message",
                    "--format=non-existing",
                ],
            )
            assert result.exit_code == 2, result.stdout
            assert report.called_once
            assert check_cache.called_once


def test_report_html_format_with_output():
    """
    Test that report calls the report command with HTML as format and specified output
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(
                main.cli,
                [
                    "report",
                    "foo.py",
                    "example_metric",
                    "-n 101",
                    "--message",
                    "--format=HTML",
                    "--output=reports/out.html",
                ],
            )

            assert result.exit_code == 0, result.stdout
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metrics"] == ("example_metric",)
            assert report.call_args[1]["include_message"]
            assert report.call_args[1]["n"] == 101
            assert report.call_args[1]["format"] == ReportFormat.HTML
            assert report.call_args[1]["output"] == Path().cwd() / Path(
                "reports/out.html"
            )


def test_graph():
    """
    Test that graph calls the graph command
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.graph.graph") as graph:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["graph", "foo.py", "example_metric"])
            assert result.exit_code == 0
            assert graph.called_once
            assert check_cache.called_once
            assert graph.call_args[1]["path"] == "foo.py"
            assert graph.call_args[1]["metrics"] == ("example_metric",)


def test_graph_multiple_metrics():
    """
    Test that graph calls the graph command with multiple metrics
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.graph.graph") as graph:
            runner = CliRunner()
            result = runner.invoke(
                main.cli, ["graph", "foo.py", "example_metric", "another_metric"]
            )
            assert result.exit_code == 0
            assert graph.called_once
            assert check_cache.called_once
            assert graph.call_args[1]["path"] == "foo.py"
            assert graph.call_args[1]["metrics"] == ("example_metric", "another_metric")


def test_graph_with_output():
    """
    Test that graph calls the graph command with output
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.graph.graph") as graph:
            runner = CliRunner()
            result = runner.invoke(
                main.cli, ["graph", "foo.py", "example_metric", "-o", "foo.html"]
            )
            assert result.exit_code == 0
            assert graph.called_once
            assert check_cache.called_once
            assert graph.call_args[1]["path"] == "foo.py"
            assert graph.call_args[1]["metrics"] == ("example_metric",)
            assert graph.call_args[1]["output"] == "foo.html"


def test_diff():
    """
    Test that diff calls the diff command
    """
    with patch(
        "wily.__main__.get_default_metrics",
        return_value=["maintainability.mi", "raw.loc"],
    ) as gdf:
        with patch("wily.__main__.exists", return_value=True) as check_cache:
            with patch("wily.commands.diff.diff") as diff:
                runner = CliRunner()
                result = runner.invoke(main.cli, ["diff", "foo.py", "x/b.py"])
                assert result.exit_code == 0
                assert diff.called_once
                assert check_cache.called_once
                assert diff.call_args[1]["files"] == ("foo.py", "x/b.py")
                assert gdf.called_once
                assert "maintainability.mi" in diff.call_args[1]["metrics"]


def test_diff_with_metrics():
    """
    Test that diff calls the diff command with additional metrics
    """
    with patch(
        "wily.__main__.get_default_metrics",
        return_value=["maintainability.mi", "raw.loc"],
    ) as gdf:
        with patch("wily.__main__.exists", return_value=True) as check_cache:
            with patch("wily.commands.diff.diff") as diff:
                runner = CliRunner()
                result = runner.invoke(
                    main.cli,
                    [
                        "diff",
                        "foo.py",
                        "x/b.py",
                        "--metrics",
                        "maintainability.mi,raw.sloc",
                    ],
                )
                assert result.exit_code == 0
                assert diff.called_once
                assert check_cache.called_once
                assert diff.call_args[1]["files"] == ("foo.py", "x/b.py")
                assert not gdf.called
                assert "maintainability.mi" in diff.call_args[1]["metrics"]
                assert "raw.loc" not in diff.call_args[1]["metrics"]


def test_clean():
    """
    Test that graph calls the clean command
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.cache.clean") as clean:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["clean", "--yes"])
            assert result.exit_code == 0
            assert clean.called_once
            assert check_cache.called_once


def test_clean_with_prompt():
    """
    Test that graph calls the clean command
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.cache.clean") as clean:
            with patch("wily.__main__.input", return_value="y") as mock_input:
                runner = CliRunner()
                result = runner.invoke(main.cli, ["clean"])
                assert result.exit_code == 0
                assert clean.called_once
                assert check_cache.called_once
                assert mock_input.called_once


def test_clean_with_prompt_no_value():
    """
    Test that graph calls the clean command and if enter type "n" it doesn't clean index
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.cache.clean") as clean:
            with patch("wily.__main__.input", return_value="n") as mock_input:
                runner = CliRunner()
                result = runner.invoke(main.cli, ["clean"])
                assert result.exit_code == 0
                assert not clean.called
                assert check_cache.called_once
                assert mock_input.called_once
