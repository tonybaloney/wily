import wily.__main__ as main
from mock import patch
from click.testing import CliRunner
from git import Repo, Actor
import pathlib
import pytest


@pytest.fixture
def builddir(tmpdir):
    """ Create a project and build it """
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

    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import abc\nfoo = 1")

    index.add(["test.py"])
    index.commit("add line", author=author, committer=committer)

    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write("import collections")

    index.add(["test.py"])
    index.commit("remove line", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", tmpdir, "build", "--target", tmpdir]
    )
    assert result.exit_code == 0, result.stdout

    return tmpdir


def test_build_not_git_repo(tmpdir):
    """
    Test that build fails in a non-git directory
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build"])
        assert result.exit_code == 1, result.stdout


def test_build_invalid_path(tmpdir):
    """
    Test that build fails with a garbage path
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", "/fo/v/a", "build"])
        assert result.exit_code == 1, result.stdout


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
        assert result.exit_code == 0, result.stdout

    cache_path = tmpdir / ".wily"
    assert cache_path.exists()


def test_report(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "report", "test.py", "raw.multi"]
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_with_message(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "report", "test.py", "raw.multi", "--message"],
        )
        assert result.exit_code == 0, result.stdout
        assert "basic test" in result.stdout
        assert "remove line" in result.stdout
        assert "Not found" not in result.stdout


def test_report_high_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "report", "test.py", "raw.loc"]
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_low_metric(builddir):
    """
    Test that report works with a build on a metric expecting high values
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "report", "test.py", "maintainability.mi"]
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_index(builddir):
    """
    Test that index works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "index"])
        assert result.exit_code == 0, result.stdout


def test_list_metrics(builddir):
    """
    Test that list-metrics works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "list-metrics"])
        assert result.exit_code == 0, result.stdout


def test_clean(builddir):
    """ Test the clean feature """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "clean", "--yes"])
        assert result.exit_code == 0, result.stdout
    cache_path = pathlib.Path(builddir) / ".wily"
    assert not cache_path.exists()


def test_graph(builddir):
    """ Test the graph feature """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "graph", "test.py", "raw.loc"]
        )
        assert result.exit_code == 0, result.stdout


def test_build_no_git_history(tmpdir):
    repo = Repo.init(path=tmpdir)
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build"])
        assert result.exit_code == 1, result.stdout


def test_index_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "index"])
        assert result.exit_code == -1, result.stdout


def test_report_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", tmpdir, "report", "test.py", "raw.loc"]
        )
        assert result.exit_code == -1, result.stdout


def test_graph_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", tmpdir, "graph", "test.py", "raw.loc"]
        )
        assert result.exit_code == -1, result.stdout


def test_clean_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "clean"])
        assert result.exit_code == -1, result.stdout


def test_graph_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "list-metrics"])
        assert result.exit_code == -1, result.stdout
