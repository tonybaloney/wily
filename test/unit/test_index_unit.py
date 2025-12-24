"""Unit tests for the index command."""

from pathlib import Path
from unittest import mock

from wily.commands.index import index


def create_mock_rows(num_revisions):
    """Create mock rows for WilyIndex."""
    rows = []
    for i in range(num_revisions):
        rows.append({
            "revision": f"abcdef{i}",
            "revision_author": f"Author {i}",
            "revision_message": f"Message {i}",
            "revision_date": i * 1000,  # Unix timestamps
            "path": "test.py",
            "path_type": "file",
        })
    return rows


class MockWilyIndex:
    """Mock WilyIndex context manager."""

    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self):
        return iter(self.rows)


def test_index_without_message(capsys):
    """Test index command outputs expected data without message."""
    mock_rows = create_mock_rows(3)
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=False)

    captured = capsys.readouterr()

    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out

    # Verify data is present
    assert "abcdef0" in captured.out
    assert "Author 0" in captured.out
    assert "abcdef1" in captured.out
    assert "Author 1" in captured.out
    assert "abcdef2" in captured.out
    assert "Author 2" in captured.out


def test_index_without_message_wrapped(capsys):
    """Test index command with wrapping enabled."""
    mock_rows = create_mock_rows(3)
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=False, wrap=True)

    captured = capsys.readouterr()

    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out

    # Verify data is present
    assert "abcdef0" in captured.out
    assert "abcdef1" in captured.out
    assert "abcdef2" in captured.out


def test_index_with_message(capsys):
    """Test index command with message column included."""
    mock_rows = create_mock_rows(3)
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=True)

    captured = capsys.readouterr()

    # Verify table headers include Message
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Message" in captured.out
    assert "Date" in captured.out

    # Verify message data is present
    assert "Message 0" in captured.out
    assert "Message 1" in captured.out
    assert "Message 2" in captured.out


def test_index_with_message_wrapped(capsys):
    """Test index command with message column and wrapping."""
    mock_rows = create_mock_rows(3)
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=True, wrap=True)

    captured = capsys.readouterr()

    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Message" in captured.out

    # Verify data is present
    assert "abcdef0" in captured.out


def test_empty_index_without_message(capsys):
    """Test index command with empty data."""
    mock_rows = []
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=False)

    captured = capsys.readouterr()

    # Verify table headers are present (empty table still has headers)
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out


def test_empty_index_with_message(capsys):
    """Test index command with empty data and message column."""
    mock_rows = []
    mock_idx = MockWilyIndex(mock_rows)

    mock_config = mock.Mock()
    mock_config.path = "/test/path"
    mock_config.archiver = "git"
    mock_config.operators = "raw"
    mock_config.cache_path = "/test/.wily"

    with mock.patch("wily.commands.index.list_archivers", return_value=["git"]):
        with mock.patch("wily.commands.index.get_default_metrics_path", return_value="/test/.wily/git/metrics.parquet"):
            with mock.patch.object(Path, "exists", return_value=True):
                with mock.patch("wily.commands.index.WilyIndex", return_value=mock_idx):
                    index(mock_config, include_message=True)

    captured = capsys.readouterr()

    # Verify table headers are present (empty table still has headers)
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Message" in captured.out
    assert "Date" in captured.out
