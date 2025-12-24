"""
Tests for the wily build command.

All of the following tests will use a click CLI runner to fully simulate the CLI.
Many of the tests will depend on a "builddir" fixture which is a compiled wily cache.

TODO : Test build + build with extra operator
"""

import pathlib
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from git.repo.base import Repo
from git.util import Actor

import wily.__main__ as main
from wily.archivers import ALL_ARCHIVERS
from wily.backend import WilyIndex

_path = "src/test.py"


def test_build_invalid_path():
    """
    Test that build fails with a garbage path
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", "/fo/v/a", "build", "test.py"])
    assert result.exit_code == 1, result.stdout


def test_build_crash(tmpdir):
    """
    Simulate a runtime error in the build.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add(["test.py"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    index.commit("basic test", author=author, committer=committer)
    repo.close()

    import wily.commands.build  # noqa: PLC0415

    # Simulate a crash by patching analyze_revision_with_index to raise an error
    with patch.object(wily.commands.build, "analyze_revision_with_index", side_effect=RuntimeError("arggh")):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert result.exit_code == 1, result.stdout


def test_build(tmpdir, cache_path):
    """
    Test that build works in a basic repository.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add(["test.py"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit("basic test", author=author, committer=committer)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", "test.py"],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    parquet_path = cache_path / "git" / "metrics.parquet"
    assert parquet_path.exists()

    # Load metrics from WilyIndex to verify contents
    with WilyIndex(str(parquet_path), ["raw"]) as wily_index:
        rows = list(wily_index)
        assert len(rows) == 2
        assert rows[0]["path"] == "test.py"
        assert rows[0]["path_type"] == "file"
        assert rows[0]["revision"] == commit.hexsha

        assert "loc" in rows[0]
        assert rows[0]["loc"] == 1  # One line of code

        # Assert directory summary
        assert rows[1]["path"] == ""
        assert rows[1]["path_type"] == "root"
        assert rows[1]["revision"] == commit.hexsha
        assert "loc" in rows[1]
        assert rows[1]["loc"] == 1  # One line of code in root


def test_build_with_config(tmpdir, cache_path):
    """
    Test that build works in a basic repository and a configuration file.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    config = """
    [wily]
    path = test.py
    operators = raw, maintainability
    """
    config_path = tmppath / "wily.cfg"
    with open(config_path, "w") as config_f:
        config_f.write(config)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add(["test.py"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    _ = index.commit("basic test", author=author, committer=committer)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--debug",
            "--config",
            str(config_path),
            "--path",
            tmpdir,
            "--cache",
            cache_path,
            "build",
        ],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    parquet_path = cache_path / "git" / "metrics.parquet"
    assert parquet_path.exists()


def test_build_twice(tmpdir, cache_path):
    """
    Test that build works when run twice.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add(["test.py"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    _ = index.commit("basic test", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", "test.py"],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path) / "git"
    assert cache_path.exists()
    parquet_path = cache_path / "metrics.parquet"
    assert parquet_path.exists()

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc\nfoo = 1")

    index.add(["test.py"])

    _ = index.commit("basic test", author=author, committer=committer)
    repo.close()

    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", "test.py"])
    assert result.exit_code == 0, result.stdout

    assert cache_path.exists()
    assert parquet_path.exists()


def test_build_no_commits(tmpdir):
    """
    Test that build fails cleanly with no commits
    """
    repo = Repo.init(path=tmpdir)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", tmpdir, "--skip-ignore-check"])
    assert result.exit_code == 1, result.stdout


def test_build_dirty_repo(builddir):
    """
    Test that build fails cleanly with a dirty repo
    """
    tmppath = pathlib.Path(builddir)
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc\nfoo = 1")

    runner = CliRunner()
    result = runner.invoke(main.cli, ["--debug", "--path", builddir, "build", builddir])
    assert result.exit_code == 1, result.stdout


def test_build_no_git_history(tmpdir):
    repo = Repo.init(path=tmpdir)
    repo.close()

    with patch("wily.logger") as _:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", _path])
        assert result.exit_code == 1, result.stdout


archivers = set(ALL_ARCHIVERS)


@pytest.mark.parametrize("archiver", archivers)
def test_build_archiver(gitdir, archiver, cache_path):
    """
    Test the build against each type of archiver
    """
    with patch("wily.logger") as _:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", gitdir, "--cache", cache_path, "build", _path, "-a", archiver],
        )
        assert result.exit_code == 0, result.stdout
        cache_path = pathlib.Path(cache_path)
        assert cache_path.exists()


def test_build_src_directory(tmpdir, cache_path):
    """
    Test that build includes files inside a directory
    """

    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()

    # Write a test file to the repo
    with open(srcpath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add([str(srcpath / "test.py")])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit("basic test", author=author, committer=committer)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", "."],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()

    parquet_path = cache_path / "git" / "metrics.parquet"
    assert parquet_path.exists()

    # Load metrics from WilyIndex to verify contents
    with WilyIndex(str(parquet_path), ["raw"]) as wily_index:
        rows = list(wily_index)
        assert len(rows) == 3

        src_path = wily_index['src/test.py']
        assert len(src_path) == 1
        assert src_path[0]["path"] == "src/test.py"
        assert src_path[0]["path_type"] == "file"
        assert src_path[0]["revision"] == commit.hexsha
        assert "loc" in src_path[0]
        assert src_path[0]["loc"] == 1  # One line of code

        root_path = wily_index['src']
        assert len(root_path) == 1
        assert root_path[0]["path"] == "src"
        assert root_path[0]["path_type"] == "directory"
        assert root_path[0]["revision"] == commit.hexsha
        assert "loc" in root_path[0]
        assert root_path[0]["loc"] == 1  # One line of code in src

        root_summary = wily_index['']
        assert len(root_summary) == 1
        assert root_summary[0]["path"] == ""
        assert root_summary[0]["path_type"] == "root"
        assert root_summary[0]["revision"] == commit.hexsha
        assert "loc" in root_summary[0]
        assert root_summary[0]["loc"] == 1  # One line of code in root
