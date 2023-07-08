from unittest.mock import patch

import pytest

from wily.archivers import Archiver, BaseArchiver, Revision
from wily.commands import build
from wily.config import DEFAULT_CONFIG
from wily.operators import BaseOperator, Operator, OperatorLevel


class MockArchiverCls(BaseArchiver):
    name = "test"

    def __init__(self, *args, **kwargs):
        pass

    def revisions(self, path, max_revisions):
        return [
            Revision(
                key="12345",
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=12_345_679,
                message="None",
                tracked_files=[],
                tracked_dirs=[],
                added_files=[],
                modified_files=[],
                deleted_files=[],
            )
        ]

    def checkout(self, revision, options):
        pass  # noop


class MockOperatorCls(BaseOperator):
    name = "test"
    data = {}

    def __init__(self, *args, **kwargs):
        pass

    def run(self, module, options):
        return self.data


MockOperator = Operator("mock", MockOperatorCls, "for testing", OperatorLevel.File)

MockArchiver = Archiver("mock", MockArchiverCls, "for testing")


@pytest.fixture
def config():
    cfg = DEFAULT_CONFIG
    return cfg


def test_build_simple(config):
    _test_operators = (MockOperator,)
    with patch("wily.state.resolve_archiver", return_value=MockArchiver):
        result = build.build(config, MockArchiver, _test_operators)
    assert result is None
