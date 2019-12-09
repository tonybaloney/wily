import pathlib
from textwrap import dedent
import shutil
import tempfile
from time import time

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

    index.commit(
        "basic test",
        author=author,
        committer=committer,
        author_date="Thu, 07 Apr 2019 22:13:13 +0200",
        commit_date="Thu, 07 Apr 2019 22:13:13 +0200",
    )

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
    index.commit(
        "add line",
        author=author,
        committer=committer,
        author_date="Mon, 10 Apr 2019 22:13:13 +0200",
        commit_date="Mon, 10 Apr 2019 22:13:13 +0200",
    )

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
    index.commit(
        "remove line",
        author=author,
        committer=committer,
        author_date="Thu, 14 Apr 2019 22:13:13 +0200",
        commit_date="Thu, 14 Apr 2019 22:13:13 +0200",
    )

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

    yield gitdir

    result1 = runner.invoke(main.cli, ["--debug", "--path", gitdir, "clean", "-y"])
    assert result1.exit_code == 0, result1.stdout


@pytest.fixture
def ipynbgitdir(tmpdir):
    """
    A fixture that provides a directory and a working Git DB,
    contains a single IPython notebook that has 3 revisions.
    """
    _NB_FOOTER = """
     "metadata": {
          "kernelspec": {
           "display_name": "Python 3",
           "language": "python",
           "name": "python3"
          },
          "language_info": {
           "codemirror_mode": {
            "name": "ipython",
            "version": 3
           },
           "file_extension": ".py",
           "mimetype": "text/x-python",
           "name": "python",
           "nbconvert_exporter": "python",
           "pygments_lexer": "ipython3",
           "version": "3.4.2"
          }
         },
     "nbformat": 4,
     "nbformat_minor": 0
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)
    testpath = tmppath / "src" / "test.ipynb"
    (tmppath / "src").mkdir()
    # Write a test file to the repo
    with open(testpath, "w") as test_txt:
        test_txt.write('{"cells": [],' + _NB_FOOTER + "}")

    index = repo.index
    index.add([str(testpath)])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    index.commit("empty notebook", author=author, committer=committer)

    first_test = (
        """{
     "cells": [
      {
       "cell_type": "code",
       "metadata": {},
       "language": "python",
       "source": [
        "import abc\\n",
        "foo = 1\\n",
        "def function1():\\n",
        "    a = 1 + 1\\n",
        "\\n",
        "class Class1(object):\\n",
        "    def method(self):\\n",
        "        b = 1 + 5\\n"
       ],
       "outputs": [],
       "execution_count": 0,
       "input": []
      }
      ],
    """
        + _NB_FOOTER
        + "}"
    )
    with open(testpath, "w") as test_txt:
        test_txt.write(dedent(first_test))

    index.add([str(testpath)])
    index.commit("single cell", author=author, committer=committer)

    second_test = (
        """{
     "cells": [
      {
       "cell_type": "code",
       "metadata": {},
       "language": "python",
       "source": [
        "import abc\\n",
        "foo = 1\\n",
        "def function1():\\n",
        "    a = 1 + 1\\n",
        "class Class1(object):\\n",
        "    def method(self):\\n",
        "        b = 1 + 5\\n",
        "        if b == 6:\\n",
        "            return 'banana'\\n"
       ],
       "outputs": [],
       "execution_count": 0,
       "input": []
      },
      {
       "cell_type": "code",
       "metadata": {},
       "language": "python",
       "source": [
        "foo = 1\\n",
        "class Class1(object):\\n",
        "    def method(self):\\n",
        "        b = 1 + 5\\n",
        "        if b == 6:\\n",
        "            return 'banana'\\n"
       ],
       "outputs": [],
       "execution_count": 0,
       "input": []
      }
      ],
    """
        + _NB_FOOTER
        + "}"
    )

    with open(testpath, "w") as test_txt:
        test_txt.write(dedent(second_test))

    index.add([str(testpath)])
    index.commit("second cell", author=author, committer=committer)

    yield tmpdir
    repo.close()


@pytest.fixture
def ipynbbuilddir(ipynbgitdir):
    """
    The ipynbgitdir fixture converted into a wily cache index.
    """
    tmppath = pathlib.Path(ipynbgitdir)

    config = """
    [wily]
    include_ipynb = true
    ipynb_cells = true
    """
    config_path = tmppath / "wily.cfg"
    with open(config_path, "w") as config_f:
        config_f.write(config)

    runner = CliRunner()
    result1 = runner.invoke(
        main.cli, ["--debug", "--path", ipynbgitdir, "build", str(tmppath / "src")]
    )
    assert result1.exit_code == 0, result1.stdout

    result2 = runner.invoke(main.cli, ["--debug", "--path", ipynbgitdir, "index"])
    assert result2.exit_code == 0, result2.stdout

    yield ipynbgitdir

    result1 = runner.invoke(main.cli, ["--debug", "--path", ipynbgitdir, "clean", "-y"])
    assert result1.exit_code == 0, result1.stdout


@pytest.fixture(autouse=True)
def cache_path(monkeypatch):
    """
    Configure wily cache and home path, clean up cache afterward
    """
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("HOME", tmp)
    yield tmp
    shutil.rmtree(tmp)
