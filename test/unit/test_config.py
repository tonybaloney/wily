import os.path

import pytest

import wily.config


def test_config_empty_defaults(tmpdir):
    """
    Test that an empty config path sets to defaults.
    """
    config = """
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w", encoding="utf8") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.max_revisions == wily.config.DEFAULT_MAX_REVISIONS


def test_config_archiver(tmpdir):
    """
    Test that an archiver can be configured
    """
    config = """
    [wily]
    archiver = foo
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w", encoding="utf8") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == "foo"
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.max_revisions == wily.config.DEFAULT_MAX_REVISIONS


@pytest.mark.parametrize(
    ("raw_operators", "expected_operators"),
    [
        ("foo,bar", ["foo", "bar"]),
        ("foo, bar", ["foo", "bar"]),
        ("foo, bar,", ["foo", "bar"]),
        ("   foo,bar   , baz", ["foo", "bar", "baz"]),
    ],
)
def test_config_operators(tmpdir, raw_operators, expected_operators):
    """
    Test that operators can be configured
    """
    config = f"""
    [wily]
    operators = {raw_operators}
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w", encoding="utf8") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == expected_operators
    assert cfg.max_revisions == wily.config.DEFAULT_MAX_REVISIONS


def test_config_max_revisions(tmpdir):
    """
    Test that an max-revisions can be configured
    """
    config = """
    [wily]
    max_revisions = 14
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w", encoding="utf8") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.max_revisions == 14


def test_config_cache_path(tmpdir):
    """
    Test that a cache-path can be configured
    """
    config = """
    [wily]
    cache_path = .wily/
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w", encoding="utf8") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.cache_path == ".wily/"
