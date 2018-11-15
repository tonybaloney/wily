import wily.__main__ as main
import wily.cache
from mock import patch
from textwrap import dedent
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

    first_test = """
    import abc
    foo = 1
    def function1():
        a = 1 + 1
    
    class Class1(object):
        def method(self):
            b = 1 + 5
    """
    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write(dedent(first_test))

    index.add(["test.py"])
    index.commit("add line", author=author, committer=committer)

    second_test = """
    import abc
    foo = 1
    def function1():
        a = 1 + 1
    class Class1(object):
        def method(self):
            b = 1 + 5
            if b == 6:
                return 'banana'
    """

    with open(tmppath / "test.py", "w") as test_txt:
        test_txt.write(dedent(second_test))

    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")

    index.add(["test.py", ".gitignore"])
    index.commit("remove line", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", tmpdir, "build", str(tmpdir)]
    )
    assert result.exit_code == 0, result.stdout

    return tmpdir


def test_build_not_git_repo(tmpdir):
    """
    Test that build fails in a non-git directory
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert result.exit_code == 1, result.stdout


def test_build_invalid_path(tmpdir):
    """
    Test that build fails with a garbage path
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", "/fo/v/a", "build", "test.py"])
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


def test_report(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "report", "test.py", "--metrics", "raw.multi"],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_granular(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "test.py:function1",
                "--metrics",
                "cyclomatic.complexity",
                "-n",
                1,
            ],
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" not in result.stdout


def test_report_not_found(builddir):
    """
    Test that report works with a build but not with an invalid path
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "report", "test1.py", "--metrics", "raw.loc"]
        )
        assert result.exit_code == 0, result.stdout
        assert "Not found" in result.stdout


def test_report_default_metrics(builddir):
    """
    Test that report works with a build
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "report", "test.py"])
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
            [
                "--path",
                builddir,
                "report",
                "test.py",
                "--metrics",
                "raw.multi",
                "--message",
            ],
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
            main.cli,
            ["--path", builddir, "report", "test.py", "--metrics", "raw.comments"],
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
            main.cli,
            [
                "--path",
                builddir,
                "report",
                "test.py",
                "--metrics",
                "maintainability.mi",
            ],
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


def test_index_with_messages(builddir):
    """
    Test that index works with a build with git commit messages
    """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "index", "--message"])
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


def test_graph_multiple(builddir):
    """ Test the graph feature with multiple metrics """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", "test.py", "raw.loc", "raw.comments"],
        )
        assert result.exit_code == 0, result.stdout


def test_graph_output(builddir):
    """ Test the graph feature with target output file """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["--path", builddir, "graph", "test.py", "raw.loc", "-o", "test.html"],
        )
        assert result.exit_code == 0, result.stdout


def test_graph_output_granular(builddir):
    """ Test the graph feature with target output file """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            [
                "--path",
                builddir,
                "graph",
                "test.py:function1",
                "cyclomatic.complexity",
                "-o",
                "test_granular.html",
            ],
        )
        assert result.exit_code == 0, result.stdout


def test_diff_output(builddir):
    """ Test the diff feature """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", builddir, "diff", "test.py"])
        assert result.exit_code == 0, result.stdout


def test_diff_output_metrics(builddir):
    """ Test the diff feature with specific metrics """
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", builddir, "diff", "test.py", "--metrics", "raw.loc"]
        )
        assert result.exit_code == 0, result.stdout


def test_build_no_git_history(tmpdir):
    repo = Repo.init(path=tmpdir)
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "build", "test.py"])
        assert result.exit_code == 1, result.stdout


def test_index_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "index"])
        assert result.exit_code == 1, result.stdout


def test_report_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "report", "test.py"])
        assert result.exit_code == 1, result.stdout


def test_graph_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["--path", tmpdir, "graph", "test.py", "raw.loc"]
        )
        assert result.exit_code == 1, result.stdout


def test_clean_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "clean"])
        assert result.exit_code == 1, result.stdout


def test_list_metrics_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "list-metrics"])
        assert result.exit_code == 1, result.stdout


def test_diff_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "diff"])
        assert result.exit_code == 1, result.stdout
