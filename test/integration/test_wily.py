import wily.__main__ as main
from mock import patch
from click.testing import CliRunner
from git import Repo, Actor
import pathlib


def test_build_not_git_repo(tmpdir):
    """
    Test that build fails in a non-git directory
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build"])
        assert result.exit_code == 1


def test_build_invalid_path(tmpdir):
    """
    Test that build fails with a garbage path
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", "/fo/v/a", "build"])
        assert result.exit_code == 1


def test_build(tmpdir):
    """
    Test that build fails in a non-git directory
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

    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build"])
        assert result.exit_code == 0

    cache_path = tmpdir / ".wily"
    assert cache_path.exists()
