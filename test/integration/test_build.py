"""
Tests for the wily build command.

All of the following tests will use a click CLI runner to fully simulate the CLI.
Many of the tests will depend on a "builddir" fixture which is a compiled wily cache.

TODO : Test build + build with extra operator
"""
import pathlib
import pytest
from click.testing import CliRunner
from git import Repo, Actor
from mock import patch

import wily.__main__ as main
from wily.archivers import ALL_ARCHIVERS


def test_build_not_git_repo(tmpdir):
    """
    Test that build defaults to filesystem in a non-git directory
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert result.exit_code == 0, result.stdout
        cache_path = tmpdir / ".wily"
        assert cache_path.exists()
        index_path = tmpdir / ".wily" / "filesystem" / "index.json"
        assert index_path.exists()


def test_build_invalid_path(tmpdir):
    """
    Test that build fails with a garbage path
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", "/fo/v/a", "build", "test.py"])
        assert result.exit_code == 1, result.stdout


def test_build_no_target(tmpdir):
    """
    Test that build fails with no target
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build"])
        assert result.exit_code == 2, result.stdout


def test_build_crash(tmpdir):
    """
    Test that build works in a basic repository.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")

    index = repo.index
    index.add(["test.py", ".gitignore"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    index.commit("basic test", author=author, committer=committer)
    import wily.commands.build

    with patch.object(
        wily.commands.build.Bar, "finish", side_effect=RuntimeError("arggh")
    ) as bar_finish:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert bar_finish.called_once
        assert result.exit_code == 1, result.stdout

    with patch("wily.commands.build.logger") as logger:
        logger.level = "DEBUG"
        with patch.object(
            wily.commands.build.Bar, "finish", side_effect=RuntimeError("arggh")
        ) as bar_finish:
            runner = CliRunner()
            result = runner.invoke(
                main.cli, ["--debug", "--path", tmpdir, "build", "test.py"]
            )
            assert bar_finish.called_once
            assert result.exit_code == 1, result.stdout


def test_build(tmpdir):
    """
    Test that build works in a basic repository.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")

    index = repo.index
    index.add(["test.py", ".gitignore"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit("basic test", author=author, committer=committer)

    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--debug", "--path", tmpdir, "build", "test.py"]
        )
        assert result.exit_code == 0, result.stdout

    cache_path = tmpdir / ".wily"
    assert cache_path.exists()
    index_path = tmpdir / ".wily" / "git" / "index.json"
    assert index_path.exists()
    rev_path = tmpdir / ".wily" / "git" / commit.name_rev.split(" ")[0] + ".json"
    assert rev_path.exists()


def test_build_twice(tmpdir):
    """
    Test that build works when run twice.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc")
    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")
    index = repo.index
    index.add(["test.py", ".gitignore"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit("basic test", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", "test.py"])
    assert result.exit_code == 0, result.stdout

    cache_path = tmpdir / ".wily"
    assert cache_path.exists()
    index_path = tmpdir / ".wily" / "git" / "index.json"
    assert index_path.exists()
    rev_path = tmpdir / ".wily" / "git" / commit.name_rev.split(" ")[0] + ".json"
    assert rev_path.exists()

    # Write a test file to the repo
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc\nfoo = 1")

    index.add(["test.py"])

    commit2 = index.commit("basic test", author=author, committer=committer)

    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", "test.py"])
    assert result.exit_code == 0, result.stdout

    cache_path = tmpdir / ".wily"
    assert cache_path.exists()
    index_path = tmpdir / ".wily" / "git" / "index.json"
    assert index_path.exists()
    rev_path = tmpdir / ".wily" / "git" / commit.name_rev.split(" ")[0] + ".json"
    assert rev_path.exists()
    rev_path2 = tmpdir / ".wily" / "git" / commit2.name_rev.split(" ")[0] + ".json"
    assert rev_path2.exists()


def test_build_no_commits(tmpdir):
    """
    Test that build fails cleanly with no commits
    """
    repo = Repo.init(path=tmpdir)

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
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "src/test.py"])
        assert result.exit_code == 1, result.stdout


archivers = {name for name in ALL_ARCHIVERS.keys()}


@pytest.mark.parametrize("archiver", archivers)
def test_build_archiver(gitdir, archiver):
    """
    Test the build against each type of archiver
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", gitdir, "build", "src/test.py", "-a", archiver]
        )
        assert result.exit_code == 0, result.stdout
        cache_path = gitdir / ".wily"
        assert cache_path.exists()
        index_path = gitdir / ".wily" / archiver / "index.json"
        assert index_path.exists()
