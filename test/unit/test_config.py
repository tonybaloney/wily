import os.path

import wily.config


def test_config_empty_defaults(tmpdir):
    """
    Test that an empty config path sets to defaults.
    """
    config = """
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w") as config_f:
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
    with open(config_path, "w") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == "foo"
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.max_revisions == wily.config.DEFAULT_MAX_REVISIONS


def test_config_operators(tmpdir):
    """
    Test that operators can be configured
    """
    config = """
    [wily]
    operators = foo,baz
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == "foo,baz"
    assert cfg.max_revisions == wily.config.DEFAULT_MAX_REVISIONS


def test_config_archiver(tmpdir):
    """
    Test that an max-revisions can be configured
    """
    config = """
    [wily]
    max_revisions = 14
    """
    config_path = os.path.join(tmpdir, "wily.cfg")
    with open(config_path, "w") as config_f:
        config_f.write(config)

    cfg = wily.config.load(config_path)

    assert cfg.archiver == wily.config.DEFAULT_ARCHIVER
    assert cfg.operators == wily.config.DEFAULT_OPERATORS
    assert cfg.max_revisions == 14
