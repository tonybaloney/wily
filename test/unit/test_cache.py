from wily.config import DEFAULT_CONFIG
import wily.cache as cache
import pathlib


def test_exists(tmpdir):
    """
    Test that exists() returns true if path does exist
    """
    config = DEFAULT_CONFIG
    config.cache_path = tmpdir
    assert cache.exists(config)


def test_not_exists():
    """
    Test that exists() returns false if path does not exist
    """
    config = DEFAULT_CONFIG
    config.cache_path = "/v/v/w"
    assert not cache.exists(config)


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
