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
            ["--path", tmpdir, "--cache", cache_path, "graph", _path, "-m", "raw.loc"],
        )
    assert result.exit_code == 1, result.stdout


def test_graph_no_path(builddir):
    """Test the graph feature with no path given"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(main.cli, ["--path", builddir, "graph", "-m", "raw.loc"])
    assert result.exit_code == 1, result.stdout


def test_graph(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "-m", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_shared_js(builddir):
    """Test the graph feature with --shared-js option"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "graph",
                _path,
                "-m",
                "raw.loc",
                "--shared-js",
            ],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_plotlyjs_cdn_js(builddir):
    """Test the graph feature with --cdn_js option"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "-m", "raw.loc", " --cdn_js"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_all(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "-m", "raw.loc", "--all"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_all_with_shorthand_metric(builddir):
    """Test the graph feature with shorthand metric"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "-m", "loc", "--all"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_changes(builddir):
    """Test the graph feature comparing changes"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", _path, "-m", "raw.loc", "--changes"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_custom_x(builddir):
    """Test the graph feature with a custom x-axis"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "-m", "raw.loc", "-x", "raw.sloc"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_aggregate(builddir):
    """Test the aggregate graphs"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "-m", "raw.loc", "--aggregate"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_individual(builddir):
    """Test individual graphs"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "-m", "raw.loc", "--individual"],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_path(builddir):
    """Test the graph feature"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "src/", "-m", "raw.loc"]
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple(builddir):
    """Test the graph feature with multiple metrics"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "-m", "raw.loc,raw.comments"],
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
                "-m",
                "raw.loc,raw.comments",
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
            main.cli,
            ["--path", builddir, "graph", "src/", "-m", "raw.loc,raw.comments"],
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
                "-m",
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
                "-m",
                "cyclomatic.complexity",
                "-o",
                "test_granular.html",
            ],
        )
    assert result.exit_code == 0, result.stdout


def test_graph_multiple_paths(builddir):
    """Test the graph feature with multiple paths"""
    runner = CliRunner()
    with patch.dict("os.environ", values=PATCHED_ENV, clear=True):
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", _path, "src/", "path3", "-m", "raw.loc"],
        )
    assert result.exit_code == 0, result.stdout
