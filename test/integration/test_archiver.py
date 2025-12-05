import pathlib

import pytest
from git.repo.base import Repo
from git.util import Actor

from wily.archivers.git import DirtyGitRepositoryError, GitArchiver
from wily.backend import get_revisions
from wily.config import DEFAULT_CONFIG


def test_rust_get_revisions_matches_python(tmpdir):
    """
    Test that the Rust get_revisions function returns the same data
    as the Python GitArchiver.revisions method.
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
    index.commit("Initial commit", author=author, committer=committer)

    # Second commit: Add more files and modify existing
    with open(tmppath / "src" / "main.py", "w") as f:
        f.write("print('hello world')")
    with open(tmppath / "src" / "utils.py", "w") as f:
        f.write("def helper(): pass")
    index.add(["src/main.py", "src/utils.py"])
    index.commit("Add utils and update main", author=author, committer=committer)

    # Third commit: Delete a file and add another
    (tmppath / "README.md").unlink()
    index.remove(["README.md"])
    with open(tmppath / "docs.md", "w") as f:
        f.write("# Documentation")
    index.add(["docs.md"])
    index.commit("Replace README with docs", author=author, committer=committer)

    repo.close()

    # Get revisions from Python implementation
    config = DEFAULT_CONFIG
    config.path = tmpdir
    archiver = GitArchiver(config)
    python_revisions = archiver.revisions(tmpdir, 10)
    archiver.finish()

    # Get revisions from Rust implementation
    rust_revisions = get_revisions(str(tmpdir), 10)

    # Validate they have the same number of revisions
    assert len(rust_revisions) == len(python_revisions)

    # Validate each revision matches
    for i, (rust_rev, py_rev) in enumerate(zip(rust_revisions, python_revisions, strict=True)):
        assert rust_rev["key"] == py_rev.key, f"Revision {i}: key mismatch"
        assert rust_rev["author_name"] == py_rev.author_name, f"Revision {i}: author_name mismatch"
        assert rust_rev["author_email"] == py_rev.author_email, f"Revision {i}: author_email mismatch"
        assert rust_rev["message"] == py_rev.message.strip(), f"Revision {i}: message mismatch"
        assert rust_rev["date"] == py_rev.date, f"Revision {i}: date mismatch"

        # File lists - sort for comparison
        assert sorted(rust_rev["tracked_files"]) == sorted(py_rev.tracked_files), \
            f"Revision {i}: tracked_files mismatch\nRust: {sorted(rust_rev['tracked_files'])}\nPython: {sorted(py_rev.tracked_files)}"
        assert sorted(rust_rev["tracked_dirs"]) == sorted(py_rev.tracked_dirs), \
            f"Revision {i}: tracked_dirs mismatch\nRust: {sorted(rust_rev['tracked_dirs'])}\nPython: {sorted(py_rev.tracked_dirs)}"
        assert sorted(rust_rev["added_files"]) == sorted(py_rev.added_files), \
            f"Revision {i}: added_files mismatch\nRust: {sorted(rust_rev['added_files'])}\nPython: {sorted(py_rev.added_files)}"
        assert sorted(rust_rev["modified_files"]) == sorted(py_rev.modified_files), \
            f"Revision {i}: modified_files mismatch\nRust: {sorted(rust_rev['modified_files'])}\nPython: {sorted(py_rev.modified_files)}"
        assert sorted(rust_rev["deleted_files"]) == sorted(py_rev.deleted_files), \
            f"Revision {i}: deleted_files mismatch\nRust: {sorted(rust_rev['deleted_files'])}\nPython: {sorted(py_rev.deleted_files)}"


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

    # === Revision 0 (commit3 - newest) ===
    rev0 = revisions[0]
    assert rev0.key == commit3.hexsha
    assert rev0.author_name == "Test Author"
    assert rev0.author_email == "test@example.com"
    assert rev0.message == "Replace README with docs"
    assert isinstance(rev0.date, int)
    assert rev0.date > 0

    # Tracked files after commit3: docs.md, src/main.py, src/utils.py
    assert sorted(rev0.tracked_files) == sorted(["docs.md", "src/main.py", "src/utils.py"])
    # Tracked dirs: root ("") and "src"
    assert "" in rev0.tracked_dirs
    assert "src" in rev0.tracked_dirs

    # Changes in commit3: added docs.md, deleted README.md
    assert rev0.added_files == ["docs.md"]
    assert rev0.modified_files == []
    assert rev0.deleted_files == ["README.md"]

    # === Revision 1 (commit2) ===
    rev1 = revisions[1]
    assert rev1.key == commit2.hexsha
    assert rev1.author_name == "Test Author"
    assert rev1.author_email == "test@example.com"
    assert rev1.message == "Add utils and update main"

    # Tracked files after commit2: README.md, src/main.py, src/utils.py
    assert sorted(rev1.tracked_files) == sorted(["README.md", "src/main.py", "src/utils.py"])

    # Changes in commit2: added src/utils.py, modified src/main.py
    assert rev1.added_files == ["src/utils.py"]
    assert rev1.modified_files == ["src/main.py"]
    assert rev1.deleted_files == []

    # === Revision 2 (commit1 - oldest) ===
    rev2 = revisions[2]
    assert rev2.key == commit1.hexsha
    assert rev2.author_name == "Test Author"
    assert rev2.author_email == "test@example.com"
    assert rev2.message == "Initial commit"

    # Tracked files after commit1: README.md, src/main.py
    assert sorted(rev2.tracked_files) == sorted(["README.md", "src/main.py"])

    # First commit: all tracked files are "added"
    assert sorted(rev2.added_files) == sorted(["README.md", "src/main.py"])
    assert rev2.modified_files == []
    assert rev2.deleted_files == []

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

    revisions = archiver.revisions(tmpdir, 3)
    assert len(revisions) == 2
    assert revisions[0].message == "commit2"
    assert revisions[0].author_email == "author@example.com"
    assert revisions[0].author_name == "An author"
    assert revisions[0].key in commit2.name_rev and revisions[0].key not in commit1.name_rev

    assert revisions[1].message == "commit1"
    assert revisions[1].author_email == "author@example.com"
    assert revisions[1].author_name == "An author"
    assert revisions[1].key in commit1.name_rev and revisions[1].key not in commit2.name_rev

    _ = archiver.checkout(revisions[1], {})

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
