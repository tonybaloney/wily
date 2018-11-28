import pathlib
from textwrap import dedent

import pytest
from click.testing import CliRunner
from git import Repo, Actor

import wily.__main__ as main


@pytest.fixture
def builddir(tmpdir):
    """ Create a project and build it """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)
    testpath = tmppath / "src" / "test.py"
    (tmppath / "src").mkdir()
    # Write a test file to the repo
    with open(testpath, "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add([str(testpath)])

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
    with open(testpath, "w") as test_txt:
        test_txt.write(dedent(first_test))

    index.add([str(testpath)])
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

    with open(testpath, "w") as test_txt:
        test_txt.write(dedent(second_test))

    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")

    index.add([str(testpath), ".gitignore"])
    index.commit("remove line", author=author, committer=committer)

    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", tmpdir, "build", str(tmppath / "src")]
    )
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "index"])
    assert result.exit_code == 0, result.stdout

    return tmpdir
