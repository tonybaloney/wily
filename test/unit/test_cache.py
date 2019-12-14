import json
import pathlib
import sys
import pytest

import wily.cache as cache
from wily.archivers import Revision
from wily.config import DEFAULT_CONFIG, ARCHIVER_GIT


def test_exists(tmpdir):
    """
    Test that exists() returns true if path does exist
    """
    config = DEFAULT_CONFIG
    config.cache_path = tmpdir
    assert cache.exists(config)


def test_exists_older(tmpdir):
    """
    Test that exists() returns true if path does exist
    and has a file with the version older than the current
    """
    config = DEFAULT_CONFIG
    tmp_path = pathlib.Path(tmpdir)
    config.cache_path = tmp_path / ".wily"
    (tmp_path / ".wily").mkdir()
    with open((tmp_path / ".wily" / "index.json"), "w+") as index:
        index.write('{"version": "0.1.0"}')
    assert cache.exists(config)


def test_not_exists():
    """
    Test that exists() returns false if path does not exist
    """
    config = DEFAULT_CONFIG
    config.cache_path = "/v/v/w"
    assert not cache.exists(config)


def test_get_default_metrics_empty(tmpdir):
    """ 
    Test that get_metrics goes ok with an empty index
    """
    config = DEFAULT_CONFIG
    tmppath = pathlib.Path(tmpdir) / ".wily"
    config.cache_path = str(tmppath)
    tmppath.mkdir()
    (tmppath / "git").mkdir()
    with open(tmppath / "git" / "index.json", "w+") as f:
        f.write("[]")

    metrics = cache.get_default_metrics(config)
    assert metrics == []


def test_create_and_delete(tmpdir):
    """
    Test that create() will create a folder with the correct path
    and then delete it.
    """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    config.cache_path = str(cache_path)
    assert not cache.exists(config)
    cache.create(config)
    assert cache.exists(config)
    cache.clean(config)
    assert not cache.exists(config)


def test_create_when_exists(tmpdir):
    """
    Test that create() will continue if the folder already exists
    """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    pathlib.Path(cache_path).mkdir()
    config.cache_path = str(cache_path)
    assert cache.exists(config)
    assert str(cache.create(config)) == str(cache_path)


def test_clean_when_not_exists(tmpdir):
    """
    Test that clean() will continue if the folder does not exist
    """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    config.cache_path = str(cache_path)
    assert not cache.exists(config)
    assert cache.clean(config) is None


def test_store_basic(tmpdir):
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    cache_path.mkdir()
    config.cache_path = cache_path
    target_path = str(pathlib.Path(tmpdir) / "foo" / "bar.py")
    _TEST_STATS = {"operator_data": {"test": {target_path: {"metric1": 1}}}}
    _TEST_REVISION = Revision(
        key="12345",
        author_name="Anthony Shaw",
        author_email="anthony@test.com",
        date="17/01/1990",
        message="my changes",
        files=[target_path],
    )
    fn = cache.store(config, ARCHIVER_GIT, _TEST_REVISION, _TEST_STATS)
    with open(fn) as cache_item:
        result = json.load(cache_item)
        assert isinstance(result, dict)
        assert result == _TEST_STATS


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_store_twice(tmpdir):
    """ Test that you can't write the same revision twice """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    cache_path.mkdir()
    config.cache_path = cache_path
    target_path = str(pathlib.Path(tmpdir) / "foo" / "bar.py")
    _TEST_STATS = {"operator_data": {"test": {target_path: {"metric1": 1}}}}
    _TEST_REVISION = Revision(
        key="12345",
        author_name="Anthony Shaw",
        author_email="anthony@test.com",
        date="17/01/1990",
        message="my changes",
        files=[target_path],
    )
    fn = cache.store(config, ARCHIVER_GIT, _TEST_REVISION, _TEST_STATS)
    with pytest.raises(RuntimeError):
        cache.store(config, ARCHIVER_GIT, _TEST_REVISION, _TEST_STATS)


def test_store_relative_paths(tmpdir):
    """
    Test that the store command works when absolute paths are used for the targets..
    """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    target_path = str(pathlib.Path(tmpdir) / "foo" / "bar.py")
    cache_path.mkdir()
    config.cache_path = cache_path
    config.path = tmpdir
    _TEST_STATS = {"operator_data": {"test": {target_path: {"metric1": 1}}}}
    _TEST_REVISION = Revision(
        key="12345",
        author_name="Anthony Shaw",
        author_email="anthony@test.com",
        date="17/01/1990",
        message="my changes",
        files=[target_path],
    )
    fn = cache.store(config, ARCHIVER_GIT, _TEST_REVISION, _TEST_STATS)
    with open(fn) as cache_item:
        result = json.load(cache_item)
        assert isinstance(result, dict)
        if sys.platform == "win32":
            assert "foo\\bar.py" in result["operator_data"]["test"].keys()
        else:
            assert "foo/bar.py" in result["operator_data"]["test"].keys()


def test_store_index(tmpdir):
    """
    Test the store index
    """
    config = DEFAULT_CONFIG
    cache_path = pathlib.Path(tmpdir) / ".wily"
    cache_path.mkdir()
    config.cache_path = cache_path
    config.path = tmpdir
    _TEST_INDEX = [{"message": "a", "date": 1234}, {"message": "b", "date": 1345}]
    fn = cache.store_archiver_index(config, ARCHIVER_GIT, _TEST_INDEX)
    with open(fn) as cache_item:
        result = json.load(cache_item)
        assert isinstance(result, list)
        assert result[0] == _TEST_INDEX[1]
