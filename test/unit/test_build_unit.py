from unittest.mock import MagicMock, mock_open, patch

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


def test_gitignore_to_radon():
    mock_file = mock_open(read_data="test1.py\n\n\\not_included\n#comment\ntest2/")
    mock_file = mock_file()
    mock_opener = MagicMock()
    mock_opener.__enter__.return_value = mock_file
    mock_opener.open.return_value = mock_opener
    mock_opener.__truediv__.return_value = mock_opener

    mock_path = MagicMock(return_value=mock_opener)
    with patch("wily.commands.build.pathlib.Path", mock_path):
        result = build.gitignore_to_radon("")
    assert result == "test1.py,test2/"
    mock_file.__iter__.assert_called_once()
    assert len(mock_opener.mock_calls) == 6


def test_gitignore_to_radon_no_gitignore():
    mock_file = mock_open(read_data="test1.py\n\n\\not_included\n#comment\ntest2/")
    mock_file = mock_file()
    mock_opener = MagicMock()
    mock_opener.__enter__.return_value = mock_file
    mock_opener.open.return_value = mock_opener
    mock_opener.__truediv__.return_value = mock_opener

    # Make gitignore_path.exists() return False
    mock_opener.exists.return_value = False
    mock_path = MagicMock(return_value=mock_opener)
    with patch("wily.commands.build.pathlib.Path", mock_path):
        result = build.gitignore_to_radon("")
    assert result == ""
    assert len(mock_opener.mock_calls) == 3
