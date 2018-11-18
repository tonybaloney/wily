import wily.__main__ as main
from mock import patch
from textwrap import dedent
from click.testing import CliRunner
from git import Repo, Actor
import pathlib
import pytest


def test_index_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "index"])
        assert result.exit_code == 1, result.stdout


def test_index(builddir):
    """
    Test that index works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "index"])
        assert result.exit_code == 0, result.stdout


def test_index_with_messages(builddir):
    """
    Test that index works with a build with git commit messages
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "index", "--message"])
        assert result.exit_code == 0, result.stdout
