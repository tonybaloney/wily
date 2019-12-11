"""
This is really an integration test.
"""
import pytest

import wily.config
import wily.state


@pytest.fixture
def config(builddir):
    _cfg = wily.config.DEFAULT_CONFIG
    _cfg.path = builddir
    return _cfg


def test_state_defaults(config):
    """ Test the state defaults """
    state = wily.state.State(config)
    assert state.index
    assert "git" in state.index
    assert state.default_archiver == "git"
    assert state.config is config


def test_index(config):
    """ Test the state index """
    state = wily.state.State(config)
    assert state.index
    assert state.index["git"] is not None

    last_revision = state.index["git"].last_revision
    assert last_revision.revision.message == "remove line"

    for revision in state.index["git"].revisions:
        assert state.index["git"][revision.revision.key]
        assert revision.revision in state.index["git"]
        assert revision.revision.key in state.index["git"]
