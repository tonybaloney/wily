import pathlib
import sys
from textwrap import dedent

import pytest
from click.testing import CliRunner

import wily.__main__ as main

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"


def test_diff_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "diff", _path])
    assert result.exit_code == 1, result.stdout


def test_diff_no_path(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "diff"])
    assert result.exit_code == 2, result.stdout


def test_diff_output(builddir):
    """ Test the diff feature with no changes """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--debug", "--path", builddir, "diff", _path])
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_all(builddir):
    """ Test the diff feature with no changes and the --all flag """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path, "--all"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout


def test_diff_output_bad_path(builddir):
    """ Test the diff feature with no changes """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", "src/baz.py"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_remove_all(builddir):
    """ Test the diff feature by removing all functions and classes """

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write("print(1)")

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path, "--all"]
    )
    assert result.exit_code == 0, result.stdout


def test_diff_output_more_complex(builddir):
    """ Test the diff feature by making the test file more complicated """

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

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(complex_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path, "--all"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "- -> -" not in result.stdout
    assert "-> -" not in result.stdout
    assert "- ->" not in result.stdout


def test_diff_output_less_complex(builddir, simple_test):
    """ Test the diff feature by making the test file more complicated """
    (pathlib.Path(builddir) / "src" / "test.py").write_text(simple_test)

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path, "--all"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "- -> -" not in result.stdout
    assert "-> -" not in result.stdout
    assert "- ->" not in result.stdout


def test_diff_output_loc(builddir):
    """ Test the diff feature by making the test file more complicated """

    simple_test = """print("test")"""

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path, "--metrics", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "10 -> \x1b[33m1\x1b[0m" in result.stdout  # 10 -> 1 (in green)


def test_diff_output_rank(builddir):
    """ Test the diff feature by making the test file more complicated """

    simple_test = """print("test")"""

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--debug",
            "--path",
            builddir,
            "diff",
            _path,
            "--all",
            "--metrics",
            "maintainability.rank",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "A -> A" in result.stdout


@pytest.mark.parametrize(
    "value, exit_code",
    [
        pytest.param(1, 1, id="Positive threshold violation"),
        pytest.param(10, 0, id="Negative threshold violation"),
    ],
)
def test_diff_with_threshold_violation(builddir, simple_test, value, exit_code):
    """ Positively test the diff threshold feature"""
    (pathlib.Path(builddir) / "src" / "test.py").write_text(simple_test)

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        f"--debug --path {builddir} diff {_path} --thresholds halstead.h1={value}".split(),
    )
    assert result.exit_code == exit_code, result.stdout
    if exit_code:
        assert "threshold violation" in result.stdout


def test_diff_with_badly_passed_thresholds(builddir, simple_test):
    """ Test correct handling of bad threshold formatting via CLI"""
    (pathlib.Path(builddir) / "src" / "test.py").write_text(simple_test)

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        f"--debug --path {builddir} diff {_path} --thresholds halstead.h1:1".split(),
    )
    assert result.exit_code == 2, result.stdout
    assert "Incorrect syntax of thresholds" in result.stdout
