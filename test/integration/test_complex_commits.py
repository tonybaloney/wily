"""
Integration tests that will create a repository with multiple files
and test the skipping of unchanged files does not impact the index.
"""

import pathlib

from click.testing import CliRunner
from git.repo.base import Repo
from git.util import Actor

import wily.__main__ as main
from wily.backend import WilyIndex

_path1 = "src/test1.py"
_path2 = "src/test2.py"


def test_skip_files(tmpdir, cache_path):
    """
    Test that only changed files are indexed in each commit.

    With the optimized build process, each revision only contains metrics
    for files that were added or modified in that specific commit.
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
    commit2 = repo.index.commit("commit the second file only", author=author, committer=committer)

    # Change the first file and commit that
    with open(tmppath / "test1.py", "w") as test2_txt:
        test2_txt.write("import zzz\nprint(1)")

    repo.index.add([str(tmppath / "test1.py")])
    commit3 = repo.index.commit("commit the first file only", author=author, committer=committer)

    repo.close()

    # build the wily cache and test its contents
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", str(tmppath)],
    )
    assert result.exit_code == 0, result.stdout

    # Check that the cache was created
    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    
    # Check that the parquet file was created
    parquet_path = cache_path / "git" / "metrics.parquet"
    assert parquet_path.exists()
    
    # Get revision keys
    rev1_key = commit.name_rev.split(" ")[0]
    rev2_key = commit2.name_rev.split(" ")[0]
    rev3_key = commit3.name_rev.split(" ")[0]
    
    # Read the parquet file using WilyIndex
    with WilyIndex(str(parquet_path), ["raw", "cyclomatic", "halstead", "maintainability"]) as idx:
        # Filter to only file entries (not directories, root, functions, etc.)
        file_rows = [row for row in idx if row["path_type"] == "file"]
        
        # Look at the first commit - both files were added
        rev1_files = [row["path"] for row in file_rows if row["revision"] == rev1_key]
        assert _path1 in rev1_files, "First commit should have test1.py (was added)"
        assert _path2 in rev1_files, "First commit should have test2.py (was added)"
        
        # Look at the second commit - only test2.py was modified
        rev2_files = [row["path"] for row in file_rows if row["revision"] == rev2_key]
        assert _path1 not in rev2_files, "Second commit should NOT have test1.py (unchanged)"
        assert _path2 in rev2_files, "Second commit should have test2.py (was modified)"
        
        # Look at the third commit - only test1.py was modified
        rev3_files = [row["path"] for row in file_rows if row["revision"] == rev3_key]
        assert _path1 in rev3_files, "Third commit should have test1.py (was modified)"
        assert _path2 not in rev3_files, "Third commit should NOT have test2.py (unchanged)"


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

    # Read the parquet file using WilyIndex
    cache_path = pathlib.Path(cache_path)
    parquet_path = cache_path / "git" / "metrics.parquet"
    assert parquet_path.exists()
    
    # Get the revision key
    rev_key = commit.name_rev.split(" ")[0]
    
    with WilyIndex(str(parquet_path), ["raw", "cyclomatic", "halstead", "maintainability"]) as idx:
        # Check the file entry exists using __getitem__
        file_rows = [row for row in idx[_path1] if row["path_type"] == "file"]
        assert len(file_rows) == 1, f"Expected one file entry for {_path1}"
        file_metrics = file_rows[0]
        
        # Check raw metrics on file (file-level totals)
        assert file_metrics["loc"] == 14
        assert file_metrics["lloc"] == 13
        assert file_metrics["sloc"] == 13
        assert file_metrics["comments"] == 0
        assert file_metrics["multi"] == 0
        assert file_metrics["blank"] == 1
        assert file_metrics["single_comments"] == 0
        
        # Check maintainability on file
        assert abs(file_metrics["mi"] - 62.3299092923013) < 0.0001
        assert file_metrics["rank"] == "A"
        
        # Check complexity on file (total)
        assert file_metrics["complexity"] == 11
        
        # Check function entries using path query
        func_path = f"{_path1}:function1"
        func_rows = idx[func_path]
        func_row = [row for row in func_rows if row["path_type"] == "function"]
        assert len(func_row) == 1, "Expected function1 entry"
        func_metrics = func_row[0]
        assert func_metrics["complexity"] == 2
        assert func_metrics["lineno"] == 4
        assert func_metrics["endline"] == 7
        assert func_metrics["is_method"] is False
        assert func_metrics["classname"] is None
        
        # Check class entries
        class_path = f"{_path1}:Class1"
        class_rows = idx[class_path]
        class_row = [row for row in class_rows if row["path_type"] == "class"]
        assert len(class_row) == 1, "Expected Class1 entry"
        class_metrics = class_row[0]
        assert class_metrics["complexity"] == 5
        assert class_metrics["real_complexity"] == 5
        assert class_metrics["lineno"] == 8
        assert class_metrics["endline"] == 14
        
        # Check method entries
        method_path = f"{_path1}:Class1.method"
        method_rows = idx[method_path]
        method_row = [row for row in method_rows if row["path_type"] == "function"]
        assert len(method_row) == 1, "Expected Class1.method entry"
        method_metrics = method_row[0]
        assert method_metrics["complexity"] == 4
        assert method_metrics["lineno"] == 9
        assert method_metrics["endline"] == 14
        assert method_metrics["is_method"] is True
        assert method_metrics["classname"] == "Class1"
        
        # Check Halstead metrics on file (aggregated totals)
        assert file_metrics["h1"] == 2
        assert file_metrics["h2"] == 9
        assert file_metrics["N1"] == 6
        assert file_metrics["N2"] == 12
        assert file_metrics["vocabulary"] == 11
        assert file_metrics["length"] == 18
        assert abs(file_metrics["volume"] - 62.2697691354714) < 0.0001
        assert abs(file_metrics["difficulty"] - 1.3333333333333333) < 0.0001
        assert abs(file_metrics["effort"] - 83.02635884729514) < 0.0001
