import pathlib

import pytest
from mock import patch

import wily.archivers
import wily.archivers.git as git
import wily.config


class MockAuthor(object):
    name = "Mr Test"
    email = "test@test.com"


class MockStats(object):
    files = {}


TEST_AUTHOR = MockAuthor()
TEST_STATS = MockStats()


class MockCommit(object):
    name_rev = "1234 bbb"
    author = TEST_AUTHOR
    committed_date = "1/1/1990"
    stats = TEST_STATS

    def __init__(self, message):
        self.message = message


class MockHead(object):
    is_detached = False


class MockRepo(object):
    active_branch = "master"
    bare = False
    _is_dirty = False
    commits = [MockCommit("commit-1"), MockCommit("commit-2")]
    head = MockHead()

    def is_dirty(self):
        return self._is_dirty

    def iter_commits(self, branch, max_count):
        assert branch == self.active_branch
        assert max_count == 99
        return self.commits


@pytest.fixture
def repo(tmpdir):
    repo = MockRepo()
    tmppath = pathlib.Path(tmpdir)
    with open(tmppath / ".gitignore", "w") as test_txt:
        test_txt.write(".wily/")
    repo.path = tmppath
    return repo


def test_basearchiver():
    archiver = wily.archivers.BaseArchiver()
    with pytest.raises(NotImplementedError):
        archiver.revisions("", 10)

    with pytest.raises(NotImplementedError):
        archiver.checkout("")


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
