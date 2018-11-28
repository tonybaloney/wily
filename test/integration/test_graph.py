from mock import patch

from click.testing import CliRunner

import wily.__main__ as main


PATCHED_ENV = {"BROWSER": "echo %s", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}


def test_graph_no_cache(tmpdir):
    runner = CliRunner()

    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", tmpdir, "graph", "src/test.py", "raw.loc"]
        )
    assert result.exit_code == 1, result.stdout


def test_graph(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/test.py", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_all(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/test.py", "raw.loc", "--all"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_changes(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", "src/test.py", "raw.loc", "--changes"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_custom_x(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", "src/test.py", "raw.loc", "-x", "raw.sloc"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_path(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple(builddir):
    """ Test the graph feature with multiple metrics """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", "src/test.py", "raw.loc", "raw.comments"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_custom_x(builddir):
    """ Test the graph feature with multiple metrics """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "graph",
                "src/test.py",
                "raw.loc",
                "raw.comments",
                "-x",
                "raw.sloc",
            ],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_path(builddir):
    """ Test the graph feature with multiple metrics """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/", "raw.loc", "raw.comments"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_output(builddir):
    """ Test the graph feature with target output file """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--debug",
                "--path",
                builddir,
                "graph",
                "src/test.py",
                "raw.loc",
                "-o",
                "test.html",
            ],
        )

    assert result.exit_code == 0, result.stdout


def test_graph_output_granular(builddir):
    """ Test the graph feature with target output file """
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--debug",
                "--path",
                builddir,
                "graph",
                "src/test.py:function1",
                "cyclomatic.complexity",
                "-o",
                "test_granular.html",
            ],
        )
    assert result.exit_code == 0, result.stdout
