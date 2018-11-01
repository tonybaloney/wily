import wily.__main__ as main
from mock import patch
from click.testing import CliRunner


def test_help():
    """
    Test that CLI when called with help options
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--help", "--debug"])
        assert result.exit_code == 0


def test_build():
    """
    Test that build calls the build command
    """
    with patch("wily.commands.build.build") as build:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["build"])
        assert result.exit_code == 0
        assert build.called_once


def test_build_with_opts():
    """
    Test that build calls the build command
    """
    with patch("wily.commands.build.build") as build:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["build", "-h 1", "-o raw,maintainability"])
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
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.commands.report.report") as report:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["report", "foo.py", "example_metric"])
            assert result.exit_code == 0
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metric"] == "example_metric"


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
            assert result.exit_code == 0
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metric"] == "example_metric"
            assert report.call_args[1]["include_message"]
            assert report.call_args[1]["n"] == 101


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
            assert graph.call_args[1]["paths"] == ["foo.py"]
            assert graph.call_args[1]["metric"] == "example_metric"


def test_clean():
    """
    Test that graph calls the graph command
    """
    with patch("wily.__main__.exists", return_value=True) as check_cache:
        with patch("wily.cache.clean") as clean:
            runner = CliRunner()
            result = runner.invoke(main.cli, ["clean", "--yes"])
            assert result.exit_code == 0
            assert clean.called_once
            assert check_cache.called_once
