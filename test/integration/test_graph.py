import sys
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

import wily.__main__ as main

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"


PATCHED_ENV = {
    "BROWSER": "echo %s",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
    "HOME": tempfile.gettempdir(),
}


def test_graph_no_cache(tmpdir, cache_path):
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", tmpdir, "--cache", cache_path, "graph", _path, "raw.loc"],
        )
    assert result.exit_code == 1, result.stdout


def test_graph(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_plotlyjs_directory(builddir):
    """Test the graph feature with plotlyjs option"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "raw.loc", "--plotlyjs", "directory"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_plotlyjs_True(builddir):
    """Test the graph feature with plotlyjs option"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "raw.loc", "--plotlyjs", "True"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_plotlyjs_False(builddir):
    """Test the graph feature with plotlyjs option"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "raw.loc", "--plotlyjs", "False"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_all(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "--all"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_all_with_shorthand_metric(builddir):
    """Test the graph feature with shorthand metric"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "loc", "--all"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_changes(builddir):
    """Test the graph feature comparing changes"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "--changes"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_custom_x(builddir):
    """Test the graph feature with a custom x-axis"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "-x", "raw.sloc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_aggregate(builddir):
    """Test the aggregate graphs"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "--aggregate"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_individual(builddir):
    """Test individual graphs"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "--individual"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_path(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple(builddir):
    """Test the graph feature with multiple metrics"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "raw.loc", "raw.comments"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_custom_x(builddir):
    """Test the graph feature with multiple metrics"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "graph",
                _path,
                "raw.loc",
                "raw.comments",
                "-x",
                "raw.sloc",
            ],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_path(builddir):
    """Test the graph feature with multiple metrics"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/", "raw.loc", "raw.comments"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_output(builddir):
    """Test the graph feature with target output file"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--debug",
                "--path",
                builddir,
                "graph",
                _path,
                "raw.loc",
                "-o",
                "test.html",
            ],
        )

    assert result.exit_code == 0, result.stdout


def test_graph_output_granular(builddir):
    """Test the graph feature with target output file"""
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
