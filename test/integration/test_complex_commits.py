"""
Integration tests that will create a repository with multiple files
and test the skipping of unchanged files does not impact the index.
"""
import json
import pathlib
import sys

import pytest
from click.testing import CliRunner
from git.repo.base import Repo
from git.util import Actor

import wily.__main__ as main

_path1 = "src\\test1.py" if sys.platform == "win32" else "src/test1.py"
_path2 = "src\\test2.py" if sys.platform == "win32" else "src/test2.py"


@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")
def test_skip_files(tmpdir, cache_path):
    """
    Test that files which were not changed are still added to each index
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir) / "src"
    tmppath.mkdir()

    # Write two test files to the repo
    with open(tmppath / "test1.py", "w") as test1_txt:
        test1_txt.write("import abc")

    with open(tmppath / "test2.py", "w") as test2_txt:
        test2_txt.write("import cde")

    index = repo.index
    index.add([str(tmppath / "test1.py"), str(tmppath / "test2.py")])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit("commit two files", author=author, committer=committer)

    # Change the second file and commit that
    with open(tmppath / "test2.py", "w") as test2_txt:
        test2_txt.write("import zzz\nprint(1)")

    repo.index.add([str(tmppath / "test2.py")])
    commit2 = repo.index.commit(
        "commit the second file only", author=author, committer=committer
    )

    # Change the first file and commit that
    with open(tmppath / "test1.py", "w") as test2_txt:
        test2_txt.write("import zzz\nprint(1)")

    repo.index.add([str(tmppath / "test1.py")])
    commit3 = repo.index.commit(
        "commit the first file only", author=author, committer=committer
    )

    repo.close()

    # build the wily cache and test its contents
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", str(tmppath)],
    )
    assert result.exit_code == 0, result.stdout

    # Check that the index files were created
    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    index_path = cache_path / "git" / "index.json"
    assert index_path.exists()
    rev_path = cache_path / "git" / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()

    # Inspect the contents of the index for the existence of both files
    with open(index_path) as index_file:
        index = json.load(index_file)

    assert len(index) == 3

    # Look at the first commit
    with open(rev_path) as rev_file:
        data = json.load(rev_file)

    assert "raw" in data["operator_data"]
    assert _path1 in data["operator_data"]["raw"]
    assert _path2 in data["operator_data"]["raw"]

    # Look at the second commit
    rev2_path = cache_path / "git" / (commit2.name_rev.split(" ")[0] + ".json")
    assert rev2_path.exists()

    with open(rev2_path) as rev2_file:
        data2 = json.load(rev2_file)

    assert "raw" in data2["operator_data"]
    assert _path1 in data2["operator_data"]["raw"]
    assert _path2 in data2["operator_data"]["raw"]

    # Look at the third commit
    rev3_path = cache_path / "git" / (commit3.name_rev.split(" ")[0] + ".json")
    assert rev3_path.exists()

    with open(rev3_path) as rev3_file:
        data3 = json.load(rev3_file)

    assert "raw" in data3["operator_data"]
    assert _path1 in data3["operator_data"]["raw"]
    assert _path2 in data3["operator_data"]["raw"]


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


def test_metric_entries(tmpdir, cache_path):
    """Test that the expected fields and values are present in metric results."""
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir) / "src"
    tmppath.mkdir()

    # Write and commit one test file to the repo
    with open(tmppath / "test1.py", "w") as test1_txt:
        test1_txt.write(complex_test)
    index = repo.index
    index.add([str(tmppath / "test1.py")])
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")
    commit = index.commit("commit one file", author=author, committer=committer)
    repo.close()

    # Build the wily cache
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", str(tmppath)],
    )
    assert result.exit_code == 0, result.stdout

    # Get the revision path and the revision data
    cache_path = pathlib.Path(cache_path)
    rev_path = cache_path / "git" / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()
    with open(rev_path) as rev_file:
        data = json.load(rev_file)

    # Check that basic data format is correct
    assert "cyclomatic" in data["operator_data"]
    assert _path1 in data["operator_data"]["cyclomatic"]
    assert "detailed" in data["operator_data"]["cyclomatic"][_path1]
    assert "total" in data["operator_data"]["cyclomatic"][_path1]

    # Test total and detailed metrics
    expected_cyclomatic_total = {"complexity": 11}
    total_cyclomatic = data["operator_data"]["cyclomatic"][_path1]["total"]
    assert total_cyclomatic == expected_cyclomatic_total

    detailed_cyclomatic = data["operator_data"]["cyclomatic"][_path1]["detailed"]
    assert "function1" in detailed_cyclomatic
    assert "lineno" in detailed_cyclomatic["function1"]
    assert "endline" in detailed_cyclomatic["function1"]
    expected_cyclomatic_function1 = {
        "name": "function1",
        "is_method": False,
        "classname": None,
        "closures": [],
        "complexity": 2,
        "loc": 3,
        "lineno": 4,
        "endline": 7,
    }
    assert detailed_cyclomatic["function1"] == expected_cyclomatic_function1

    expected_cyclomatic_Class1 = {
        "name": "Class1",
        "inner_classes": [],
        "real_complexity": 5,
        "complexity": 5,
        "loc": 6,
        "lineno": 8,
        "endline": 14,
    }
    assert detailed_cyclomatic["Class1"] == expected_cyclomatic_Class1

    expected_cyclomatic_method = {
        "name": "method",
        "is_method": True,
        "classname": "Class1",
        "closures": [],
        "complexity": 4,
        "loc": 5,
        "lineno": 9,
        "endline": 14,
    }
    assert detailed_cyclomatic["Class1.method"] == expected_cyclomatic_method

    expected_halstead_total = {
        "h1": 2,
        "h2": 3,
        "N1": 2,
        "N2": 4,
        "vocabulary": 5,
        "volume": 13.931568569324174,
        "length": 6,
        "effort": 18.575424759098897,
        "difficulty": 1.3333333333333333,
        "lineno": None,
        "endline": None,
    }
    total_halstead = data["operator_data"]["halstead"][_path1]["total"]
    assert total_halstead == expected_halstead_total

    detailed_halstead = data["operator_data"]["halstead"][_path1]["detailed"]
    assert "function1" in detailed_halstead
    assert "lineno" in detailed_halstead["function1"]
    assert detailed_halstead["function1"]["lineno"] is not None
    assert "endline" in detailed_halstead["function1"]
    if sys.version_info >= (3, 8):
        # FuncDef is missing end_lineno in Python 3.7
        assert detailed_halstead["function1"]["endline"] is not None

    assert "Class1" not in detailed_halstead

    assert "Class1.method" in detailed_halstead
    assert "lineno" in detailed_halstead["Class1.method"]
    assert detailed_halstead["Class1.method"]["lineno"] is not None
    assert "endline" in detailed_halstead["Class1.method"]
    if sys.version_info >= (3, 8):
        assert detailed_halstead["Class1.method"]["endline"] is not None

    expected_raw_total = {
        "loc": 14,
        "lloc": 13,
        "sloc": 13,
        "comments": 0,
        "multi": 0,
        "blank": 1,
        "single_comments": 0,
    }
    total_raw = data["operator_data"]["raw"][_path1]["total"]
    assert total_raw == expected_raw_total

    expected_maintainability = {"mi": 62.3299092923013, "rank": "A"}
    total_maintainability = data["operator_data"]["maintainability"][_path1]["total"]
    assert total_maintainability == expected_maintainability
