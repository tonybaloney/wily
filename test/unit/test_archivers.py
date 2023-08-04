import pathlib
from unittest.mock import patch

import pytest

import wily.archivers
import wily.config
from wily.archivers import git


class MockAuthor:
    name = "Mr Test"
    email = "test@test.com"


class MockStats:
    files = {}


TEST_AUTHOR = MockAuthor()
TEST_STATS = MockStats()


class MockCommit:
    name_rev = "1234 bbb"
    author = TEST_AUTHOR
    committed_date = "1/1/1990"
    stats = TEST_STATS
    hexsha = "123abc"
    parents = []

    def __init__(self, message):
        self.message = message


class MockHead:
    is_detached = False


class MockRepo:
    active_branch = "master"
    bare = False
    _is_dirty = False
    commits = [MockCommit("commit-1"), MockCommit("commit-2")]
    head = MockHead()

    def is_dirty(self):
        return self._is_dirty

    def iter_commits(self, branch, max_count, reverse):
        assert branch == self.active_branch
        assert max_count == 99
        assert reverse is True
        return reversed(self.commits)


class MockGit:
    def checkout(self, *args):
        ...

    def execute(self, command, *args, **kwargs):
        if command[1] == "ls-tree":
            assert command[-1] == "123abc"
            return "\n"


@pytest.fixture
def repo(tmpdir):
    repo = MockRepo()
    tmppath = pathlib.Path(tmpdir)
    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")
    repo.path = tmppath
    repo.git = MockGit()
    return repo


def test_basearchiver():
    wily.archivers.BaseArchiver(None)


def test_defaults():
    assert wily.archivers.ARCHIVER_GIT in wily.archivers.ALL_ARCHIVERS.values()


def test_resolve_archiver():
    archiver = wily.archivers.resolve_archiver("git")
    assert archiver == wily.archivers.ARCHIVER_GIT
    assert archiver.name == "git"


def test_bad_resolve_archiver():
    with pytest.raises(ValueError):
        wily.archivers.resolve_archiver("baz")


def test_git_init(repo):
    with patch("wily.archivers.git.Repo", return_value=repo):
        test_config = wily.config.DEFAULT_CONFIG
        test_config.path = repo.path
        archiver = git.GitArchiver(test_config)
        assert archiver.repo is not None
        assert archiver.config == test_config


def test_git_revisions(repo, tmpdir):
    with patch("wily.archivers.git.Repo", return_value=repo):
        test_config = wily.config.DEFAULT_CONFIG
        test_config.path = repo.path
        archiver = git.GitArchiver(test_config)
        revisions = archiver.revisions(tmpdir, 99)
        assert archiver.repo is not None
        assert archiver.config == test_config
        assert revisions[0].key == "1234"
        assert revisions[1].key == "1234"
        assert revisions[0].author_name == "Mr Test"
