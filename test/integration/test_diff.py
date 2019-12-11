import pathlib
import sys
from textwrap import dedent

from click.testing import CliRunner

import wily.__main__ as main

_path = "src\\test.py" if sys.platform == "win32" else "src/test.py"


def test_diff_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", tmpdir, "diff", _path], catch_exceptions=False
    )
    assert result.exit_code == 1, result.stdout


def test_diff_no_path(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "diff"], catch_exceptions=False)
    assert result.exit_code == 2, result.stdout


def test_diff_output(builddir):
    """ Test the diff feature with no changes """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", _path], catch_exceptions=False
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_all(builddir):
    """ Test the diff feature with no changes and the --all flag """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout


def test_diff_output_bad_path(builddir):
    """ Test the diff feature with no changes """
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", "src/baz.py"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_remove_all(builddir):
    """ Test the diff feature by removing all functions and classes """

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write("print(1)")

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
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
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "- -> -" not in result.stdout
    assert "-> -" not in result.stdout
    assert "- ->" not in result.stdout


def test_diff_output_less_complex(builddir):
    """ Test the diff feature by making the test file more complicated """

    simple_test = """
            import abc
            foo = 1
            def function1():
                pass
            class Class1(object):
                def method(self):
                    pass
            """

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
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
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--metrics", "raw.loc"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "10 -> \x1b[33m1\x1b[0m" in result.stdout  # 10 -> 1 (in green)


def test_diff_output_loc_and_revision(builddir):
    """ Test the diff feature by making the test file more complicated, particular revision """

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
            "--metrics",
            "raw.loc",
            "-r",
            "HEAD^1",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "9 -> \x1b[33m1\x1b[0m" in result.stdout  # 10 -> 1 (in green)


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
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "A -> A" in result.stdout
