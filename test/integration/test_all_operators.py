"""
Parameterised tests for each operator (and some combinations).

Build them and test out some of the metrics/commands work correctly.
"""
import pytest
import sys
from click.testing import CliRunner
import pathlib
from textwrap import dedent

from git import Repo, Actor

import wily.__main__ as main

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"

operators = (
    "halstead",
    "cyclomatic",
    "maintainability",
    "raw",
    "halstead,cyclomatic",
    "maintainability,raw",
    "halstead,cyclomatic,maintainability,raw",
)


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
@pytest.mark.parametrize("operator", operators)
def test_operator(operator, gitdir):
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", gitdir, "build", "src", "-o", operator],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "report", _path], catch_exceptions=False
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli,
        ["--debug", "--path", gitdir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout

    complex_test = """
            import abc
            foo = 1
            def function1():
                a = 1 + 1
                if a == 2:
                    print(1)
            class Class1(object):
                def method(self):
                    b = 1 + 5
                    if b == 6:
                        if 1==2:
                           if 2==3:
                              print(1)
            """

    with open(pathlib.Path(gitdir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(complex_test))

    result = runner.invoke(
        main.cli,
        ["--debug", "--path", gitdir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout


@pytest.mark.parametrize("operator", operators)
def test_operator_on_code_with_metric_named_objects(operator, tmpdir):
    code_with_metric_named_objects = """

    # CyclomaticComplexity
    def complexity(): pass

    # Halstead
    def h1(): pass
    def h2(): pass
    def N1(): pass
    def N2(): pass
    def vocabulary(): pass
    def length(): pass
    def volume(): pass
    def difficulty(): pass
    def error(): pass

    # Maintainability
    def rank(): pass
    def mi(): pass

    # RawMetrics
    def loc(): pass
    def lloc(): pass
    def sloc(): pass
    def comments(): pass
    def multi(): pass
    def blank(): pass
    def single_comments(): pass

    """

    testpath = pathlib.Path(tmpdir) / "test.py"
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    with open(testpath, "w") as test_py:
        test_py.write(dedent(code_with_metric_named_objects))

    with Repo.init(path=tmpdir) as repo:
        repo.index.add(["test.py"])
        repo.index.commit("add test.py", author=author, committer=committer)

    runner = CliRunner()

    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "build", str(testpath), "-o", operator],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
