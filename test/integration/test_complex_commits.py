"""
Integration tests that will create a repository with multiple files
and test the skipping of unchanged files does not impact the index.
"""
import pathlib
import json
from click.testing import CliRunner
from git import Repo, Actor

import wily.__main__ as main


def test_skip_files(tmpdir, cache_path):
    """
    Test that build works in a basic repository.
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
    repo.close()

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", tmpdir, "--cache", cache_path, "build", "src"],
    )
    assert result.exit_code == 0, result.stdout

    cache_path = pathlib.Path(cache_path)
    assert cache_path.exists()
    index_path = cache_path / "git" / "index.json"
    assert index_path.exists()
    rev_path = cache_path / "git" / (commit.name_rev.split(" ")[0] + ".json")
    assert rev_path.exists()

    with open(index_path) as index_file:
        index = json.load(index_file)

    assert len(index) == 1
    assert index[0]['files'] == ['src/test1.py', 'src/test2.py']

    with open(rev_path) as rev_file:
        data = json.load(rev_file)

    assert "halstead" in data["operator_data"]
