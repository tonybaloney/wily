import wily.__main__ as main
from click.testing import CliRunner


def test_graph_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", tmpdir, "graph", "src/test.py", "raw.loc"]
    )
    assert result.exit_code == 1, result.stdout


def test_graph(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "graph", "src/test.py", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout


def test_graph_path(builddir):
    """ Test the graph feature """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "graph", "src/", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple(builddir):
    """ Test the graph feature with multiple metrics """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "graph", "src/test.py", "raw.loc", "raw.comments"],
    )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_path(builddir):
    """ Test the graph feature with multiple metrics """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "graph", "src/", "raw.loc", "raw.comments"],
    )
    assert result.exit_code == 0, result.stdout


def test_graph_output(builddir):
    """ Test the graph feature with target output file """
    runner = CliRunner()
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
