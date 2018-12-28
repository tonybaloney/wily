import pathlib
from textwrap import dedent
import os
import shutil
import tempfile
import pytest
from click.testing import CliRunner
from git import Repo, Actor

import wily.__main__ as main


@pytest.fixture
def gitdir(tmpdir):
    """ Create a project and add code to it """
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

    index.add([str(testpath)])
    index.commit("remove line", author=author, committer=committer)

    yield tmpdir
    repo.close()


@pytest.fixture
def builddir(gitdir):
    """
    A directory with a wily cache
    """
    tmppath = pathlib.Path(gitdir)
    runner = CliRunner()
    result1 = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "build", str(tmppath / "src")]
    )
    assert result1.exit_code == 0, result1.stdout

    result2 = runner.invoke(main.cli, ["--debug", "--path", gitdir, "index"])
    assert result2.exit_code == 0, result2.stdout

    return gitdir


@pytest.fixture(autouse=True)
def cache_path(monkeypatch):
    """
    Configure wily cache and home path, clean up cache afterward
    """
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("HOME", tmp)
    yield tmp
    shutil.rmtree(tmp)
