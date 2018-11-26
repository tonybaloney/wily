import wily.__main__ as main
from mock import patch
from textwrap import dedent
from click.testing import CliRunner
import pathlib


def test_diff_no_cache(tmpdir):
    with patch("wily.logger") as logger:
        runner = CliRunner()
        result = runner.invoke(main.cli, ["--path", tmpdir, "diff"])
        assert result.exit_code == 2, result.stdout


def test_diff_output(builddir):
    """ Test the diff feature with no changes """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", "src/test.py"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_all(builddir):
    """ Test the diff feature with no changes and the --all flag """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", builddir, "diff", "src/test.py", "--all"]
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
        main.cli, ["--debug", "--path", builddir, "diff", "src/test.py", "--all"]
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
        main.cli, ["--debug", "--path", builddir, "diff", "src/test.py", "--all"]
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
        main.cli, ["--debug", "--path", builddir, "diff", "src/test.py", "--all"]
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "- -> -" not in result.stdout
    assert "-> -" not in result.stdout
    assert "- ->" not in result.stdout
