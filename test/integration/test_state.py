"""
This is really an integration test.
"""

import os.path

import pytest

import wily.config
import wily.state


@pytest.fixture
def config(builddir):
    _cfg = wily.config.DEFAULT_CONFIG
    _cfg.path = builddir
    _cfg.cache_path = os.path.join(builddir, wily.config.DEFAULT_CACHE_PATH)
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
    assert len(state.index["git"]) == 3
    assert len(state.index["git"].revision_keys) == 3
    for revision in state.index["git"].revisions:
        assert state.index["git"][revision.revision.key]
        assert revision.revision in state.index["git"]
        assert revision.revision.key in state.index["git"]
