import pathlib

import pytest
from git.repo.base import Repo
from git.util import Actor

from wily.archivers.git import DirtyGitRepositoryError, GitArchiver
from wily.config import DEFAULT_CONFIG


def test_git_revisions_all_fields(tmpdir):
    """
    Comprehensive test validating all fields of Revision for the git archiver.

    This test creates a git repo with multiple commits that include:
    - Adding files
    - Modifying files
    - Deleting files
    - Subdirectories

    And validates all Revision fields are correctly populated.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    index = repo.index
    author = Actor("Test Author", "test@example.com")
    committer = Actor("Test Committer", "committer@example.com")

    # First commit: Add initial files
    (tmppath / "src").mkdir()
    with open(tmppath / "README.md", "w") as f:
        f.write("# Test Project")
    with open(tmppath / "src" / "main.py", "w") as f:
        f.write("print('hello')")
    index.add(["README.md", "src/main.py"])
    commit1 = index.commit("Initial commit", author=author, committer=committer)

    # Second commit: Add more files and modify existing
    with open(tmppath / "src" / "main.py", "w") as f:
        f.write("print('hello world')")
    with open(tmppath / "src" / "utils.py", "w") as f:
        f.write("def helper(): pass")
    index.add(["src/main.py", "src/utils.py"])
    commit2 = index.commit("Add utils and update main", author=author, committer=committer)

    # Third commit: Delete a file and add another
    (tmppath / "README.md").unlink()
    index.remove(["README.md"])
    with open(tmppath / "docs.md", "w") as f:
        f.write("# Documentation")
    index.add(["docs.md"])
    commit3 = index.commit("Replace README with docs", author=author, committer=committer)

    repo.close()

    config = DEFAULT_CONFIG
    config.path = tmpdir

    archiver = GitArchiver(config)
    revisions = archiver.revisions(tmpdir, 10)

    # Should have 3 revisions, newest first
    assert len(revisions) == 3

    revisions = list(revisions)

    # === Revision 2 (commit3 - newest) ===
    rev2 = revisions[2]
    assert rev2["key"] == commit3.hexsha
    assert rev2["author_name"] == "Test Author"
    assert rev2["author_email"] == "test@example.com"
    assert rev2["message"] == "Replace README with docs"
    assert isinstance(rev2["date"], int)
    assert rev2["date"] > 0

    # Changes in commit3: added docs.md, deleted README.md
    assert rev2["added_files"] == [] # Empty because no Python files added
    assert rev2["modified_files"] == []
    assert rev2["deleted_files"] == [] # Empty because no Python files deleted

    # === Revision 1 (commit2) ===
    rev1 = revisions[1]
    assert rev1["key"] == commit2.hexsha
    assert rev1["author_name"] == "Test Author"
    assert rev1["author_email"] == "test@example.com"
    assert rev1["message"] == "Add utils and update main"

    # Changes in commit2: added src/utils.py, modified src/main.py
    assert rev1["added_files"] == ["src/utils.py"]
    assert rev1["modified_files"] == ["src/main.py"]
    assert rev1["deleted_files"] == []

    # === Revision 2 (commit1 - oldest) ===
    rev0 = revisions[0]
    assert rev0["key"] == commit1.hexsha
    assert rev0["author_name"] == "Test Author"
    assert rev0["author_email"] == "test@example.com"
    assert rev0["message"] == "Initial commit"
    # First commit: all tracked files are "added"
    assert sorted(rev0["added_files"]) == sorted(["src/main.py"])
    assert rev0["modified_files"] == []
    assert rev0["deleted_files"] == []
    archiver.finish()


def test_git_end_to_end(tmpdir):
    """
    Complete end-to-end test of the git integration
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    index = repo.index
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    # First commit
    with open(tmppath / ".gitignore", "w") as ignore:
        ignore.write(".wily/")
    index.add([".gitignore"])
    commit1 = index.commit("commit1", author=author, committer=committer)

    # Second commit
    with open(tmppath / "test.py", "w") as file1:
        file1.write("print(1)")
    index.add(["test.py"])
    commit2 = index.commit("commit2", author=author, committer=committer)
    repo.close()

    config = DEFAULT_CONFIG
    config.path = tmpdir

    archiver = GitArchiver(config)
    assert archiver.config == config

    revisions = list(archiver.revisions(tmpdir, 3))
    assert len(revisions) == 2

    assert revisions[0]["message"] == "commit1"
    assert revisions[0]["author_email"] == "author@example.com"
    assert revisions[0]["author_name"] == "An author"
    assert revisions[0]["key"] in commit1.name_rev and revisions[0]["key"] not in commit2.name_rev

    assert revisions[1]["message"] == "commit2"
    assert revisions[1]["author_email"] == "author@example.com"
    assert revisions[1]["author_name"] == "An author"
    assert revisions[1]["key"] in commit2.name_rev and revisions[1]["key"] not in commit1.name_rev


    _ = archiver.checkout(revisions[0], {})

    assert not (tmppath / "test.py").exists()

    _ = archiver.finish()

    assert (tmppath / "test.py").exists()


def test_dirty_git(tmpdir):
    """Check that repository fails to initialise if unchecked files are in the repo"""
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    index = repo.index
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    # First commit
    with open(tmppath / ".gitignore", "w") as ignore:
        ignore.write(".wily/")

    index.add([".gitignore"])
    _ = index.commit("commit1", author=author, committer=committer)

    # Write a test file to the repo
    with open(tmppath / "blah.py", "w") as ignore:
        ignore.write("*.py[co]\n")
    index.add(["blah.py"])
    repo.close()

    config = DEFAULT_CONFIG
    config.path = tmpdir

    with pytest.raises(DirtyGitRepositoryError):
        archiver = GitArchiver(config)
        archiver.revisions(tmpdir, 2)


def test_detached_head(tmpdir):
    """Check that repo can initialize in detached head state"""
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    index = repo.index
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    # First commit
    with open(tmppath / "test.py", "w") as ignore:
        ignore.write("print('hello world')")

    index.add(["test.py"])
    _ = index.commit("commit1", author=author, committer=committer)

    # Second commit
    with open(tmppath / "test.py", "w") as ignore:
        ignore.write("print('hello world')\nprint(1)")

    index.add(["test.py"])
    commit2 = index.commit("commit2", author=author, committer=committer)

    repo.git.checkout(commit2.hexsha)
    repo.close()

    config = DEFAULT_CONFIG
    config.path = tmpdir

    archiver = GitArchiver(config)
    assert archiver.revisions(tmpdir, 1) is not None
