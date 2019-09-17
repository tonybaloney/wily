"""
Tests for the wily build command.

All of the following tests will use a click CLI runner to fully simulate the CLI.
Many of the tests will depend on a "builddir" fixture which is a compiled wily cache.

TODO : Test build + build with extra operator
"""
import sys
import pathlib
import pytest
from click.testing import CliRunner
from git import Repo, Actor
from mock import patch

import wily.__main__ as main
from wily.archivers import ALL_ARCHIVERS
from wily.config import generate_cache_path

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"


def test_build_not_git_repo(tmpdir, cache_path):
    """
    Test that build defaults to filesystem in a non-git directory
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", tmpdir, "--cache", cache_path, "build", "test.py"]
    )
    assert result.exit_code == 0, result.stdout
    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    index_path = cache_path / "filesystem" / "index.json"
    assert index_path.exists()


def test_build_custom_cache(tmpdir):
    """
    Test that build defaults to filesystem in a non-git directory with custom cache path.
    """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", tmpdir, "--cache", tmpdir / ".wily", "build", "test.py"]
    )
    assert result.exit_code == 0, result.stdout
    cache_path = tmpdir / ".wily"
    assert cache_path.exists()
    index_path = cache_path / "filesystem" / "index.json"
    assert index_path.exists()
    assert not pathlib.Path(generate_cache_path(tmpdir)).exists()


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

    import wily.commands.build

    with patch.object(
        wily.commands.build.Bar, "finish", side_effect=RuntimeError("arggh")
    ) as bar_finish:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert bar_finish.called_once
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
    index_path = cache_path / "git" / "index.json"
    assert index_path.exists()
    rev_path = cache_path / "git" / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_build_with_config(tmpdir, cache_path):
    """
    Test that build works in a basic repository and a configuration file.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    config = """
    [wily]
    path = test.py
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

    commit = index.commit("basic test", author=author, committer=committer)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--debug",
            "--config",
            config_path,
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
    index_path = cache_path / "git" / "index.json"
    assert index_path.exists()
    rev_path = cache_path / "git" / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()


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

    commit = index.commit("basic test", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", "test.py"],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path) / "git"
    assert cache_path.exists()
    index_path = cache_path / "index.json"
    assert index_path.exists()
    rev_path = cache_path / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc\nfoo = 1")

    index.add(["test.py"])

    commit2 = index.commit("basic test", author=author, committer=committer)
    repo.close()

    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", "test.py"])
    assert result.exit_code == 0, result.stdout

    assert cache_path.exists()
    index_path = cache_path / "index.json"
    assert index_path.exists()
    rev_path = cache_path / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()
    rev_path2 = cache_path / (commit2.name_rev.split(" ")[0] + ".json")
    assert rev_path2.exists()


def test_build_no_commits(tmpdir):
    """
    Test that build fails cleanly with no commits
    """
    repo = Repo.init(path=tmpdir)
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", tmpdir, "build", tmpdir, "--skip-ignore-check"]
    )
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

    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", _path])
        assert result.exit_code == 1, result.stdout


archivers = {name for name in ALL_ARCHIVERS.keys()}


@pytest.mark.parametrize("archiver", archivers)
def test_build_archiver(gitdir, archiver, cache_path):
    """
    Test the build against each type of archiver
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", gitdir, "--cache", cache_path, "build", _path, "-a", archiver],
        )
        assert result.exit_code == 0, result.stdout
        cache_path = pathlib.Path(cache_path)
        assert cache_path.exists()
        index_path = cache_path / archiver / "index.json"
        assert index_path.exists()
