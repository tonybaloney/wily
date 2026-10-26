import os
import pathlib
import subprocess
import sys

from click.testing import CliRunner

import wily.__main__ as main


def test_list_metrics(builddir):
    """
    Test that list-metrics works with a build
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "list-metrics"])
    assert result.exit_code == 0, result.stdout


def test_clean(builddir):
    """Test the clean feature"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "clean", "--yes"])
    assert result.exit_code == 0, result.stdout
    cache_path = pathlib.Path(builddir) / ".wily"
    assert not cache_path.exists()


def test_clean_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "clean"])
    assert result.exit_code == 0, result.stdout


def test_list_metrics_no_cache(tmpdir):
    """list-metrics lists static metrics and does not require a cache."""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "list-metrics"])
    assert result.exit_code == 0, result.stdout
    assert "cyclomatic" in result.stdout


def test_version_on_non_utf8_stdout():
    """--version and --help must not crash when stdout can't encode the emoji (#265)."""
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    env.pop("PYTHONUTF8", None)
    for arg, expected in (("--version", b"version 2"), ("--help", b"Inspect and search")):
        result = subprocess.run([sys.executable, "-m", "wily", arg], capture_output=True, env=env, check=False)  # noqa: S603
        assert result.returncode == 0, result.stderr.decode("cp1252", "replace")
        assert expected in result.stdout
