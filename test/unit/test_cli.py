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
            main.cli, ["build", "wily", "-h 1", "-o raw,maintainability"]
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
                main.cli,
                [
                    "report",
                    "foo.py",
                    "--metrics",
                    "example_metric",
                    "-n 101",
                    "--message",
                ],
            )
            assert result.exit_code == 0, result.stdout
            assert report.called_once
            assert check_cache.called_once
            assert report.call_args[1]["path"] == "foo.py"
            assert report.call_args[1]["metrics"] == ["example_metric"]
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
            assert graph.call_args[1]["paths"] == ["foo.py"]
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
            assert graph.call_args[1]["paths"] == ["foo.py"]
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
