import pathlib
from git import Repo, Actor
import pytest
from wily.config import DEFAULT_CONFIG
from wily.archivers.git import (
    GitArchiver,
    WilyIgnoreGitRepositoryError,
    DirtyGitRepositoryError,
)


def test_gitignore_missing(tmpdir):
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / ".gitignore", "w") as ignore:
        ignore.write("*.py[co]\n")

    index = repo.index
    index.add([".gitignore"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    index.commit("ignore python cache", author=author, committer=committer)

    config = DEFAULT_CONFIG
    config.path = tmpdir

    with pytest.raises(WilyIgnoreGitRepositoryError):
        archiver = GitArchiver(config)


gitignore_combinations = (".wily/", ".wily", ".wily/*")


@pytest.mark.parametrize("ignore", gitignore_combinations)
def test_gitignore(tmpdir, ignore, **kwargs):
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)

    # Write a test file to the repo
    with open(tmppath / ".gitignore", "w") as ignore_f:
        ignore_f.write(ignore)

    index = repo.index
    index.add([".gitignore"])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    index.commit("ignore python cache", author=author, committer=committer)

    config = DEFAULT_CONFIG
    config.path = tmpdir

    archiver = GitArchiver(config)
    assert archiver.config == config


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

    config = DEFAULT_CONFIG
    config.path = tmpdir

    archiver = GitArchiver(config)
    assert archiver.config == config

    revisions = archiver.revisions(tmpdir, 3)
    assert len(revisions) == 2
    assert revisions[0].message == "commit2"
    assert revisions[0].author_email == "author@example.com"
    assert revisions[0].author_name == "An author"
    assert (
        revisions[0].key in commit2.name_rev
        and revisions[0].key not in commit1.name_rev
    )

    assert revisions[1].message == "commit1"
    assert revisions[1].author_email == "author@example.com"
    assert revisions[1].author_name == "An author"
    assert (
        revisions[1].key in commit1.name_rev
        and revisions[1].key not in commit2.name_rev
    )

    checkout = archiver.checkout(revisions[1], None)

    assert not (tmppath / "test.py").exists()

    finish = archiver.finish()

    assert (tmppath / "test.py").exists()


def test_dirty_git(tmpdir):
    """ Check that repository fails to initialise if unchecked files are in the repo """
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

    # Write a test file to the repo
    with open(tmppath / "blah.py", "w") as ignore:
        ignore.write("*.py[co]\n")
    index.add(["blah.py"])

    config = DEFAULT_CONFIG
    config.path = tmpdir

    with pytest.raises(DirtyGitRepositoryError):
        archiver = GitArchiver(config)
        archiver.revisions(tmpdir, 2)
