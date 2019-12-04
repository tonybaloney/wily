"""
Integration tests that will create a repository with multiple files
and test the skipping of unchanged files does not impact the index.
"""
import sys
import pathlib
import json
from click.testing import CliRunner
from git import Repo, Actor

import wily.__main__ as main

_path1 = "src\\test1.py" if sys.platform == "win32" else "src/test1.py"
_path2 = "src\\test2.py" if sys.platform == "win32" else "src/test2.py"


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
