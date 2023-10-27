import os
import sys
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
                tracked_files=["a", "b", "c"],
                tracked_dirs=["d"],
                added_files=[],
                modified_files=[],
                deleted_files=[],
            ),
            Revision(
                key="67890",
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=12_345_679,
                message="None again",
                tracked_files=["a", "b", "c", "d"],
                tracked_dirs=["d"],
                added_files=["e"],
                modified_files=["f"],
                deleted_files=["a"],
            ),
        ]

    def checkout(self, revision, options):
        pass  # noop


class MockOperatorCls(BaseOperator):
    name = "test"
    data = {"C:\\home\\test1.py" if sys.platform == "win32" else "/home/test1.py": None}

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
    with patch("wily.state.resolve_archiver", return_value=MockArchiver), patch(
        "wily.commands.build.resolve_operator", return_value=MockOperator
    ):
        result = build.build(config, MockArchiver, _test_operators)  # type: ignore
    assert result is None


def test_run_operator(config):
    rev = Revision("123", None, None, 1, "message", [], [], [], [], [])
    name, data = build.run_operator(MockOperator, rev, config, ["test1.py"])
    assert name == "mock"
    path = "C:\\home\\test1.py" if sys.platform == "win32" else "/home/test1.py"
    assert data == {os.path.relpath(path, config.path): None}
