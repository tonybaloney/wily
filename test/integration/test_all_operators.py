"""
Parameterised tests for each operator (and some combinations).

Build them and test out some of the metrics/commands work correctly.
"""
import pytest
from click.testing import CliRunner
import pathlib
from textwrap import dedent

import wily.__main__ as main

operators = (
    "halstead",
    "cyclomatic",
    "maintainability",
    "raw",
    "halstead,cyclomatic",
    "maintainability,raw",
    "halstead,cyclomatic,maintainability,raw",
)


@pytest.mark.parametrize("operator", operators)
def test_operator(operator, gitdir):
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "build", "src", "-o", operator]
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "report", "src/test.py"]
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "diff", "src/test.py", "--all"]
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
        main.cli, ["--debug", "--path", gitdir, "diff", "src/test.py", "--all"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
