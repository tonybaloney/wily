"""Unit tests for the rank command."""

from unittest import mock

from util import get_mock_state_and_config

from wily.commands.rank import rank


def test_rank(capsys):
    """Test rank command outputs expected data."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=0,
            threshold=0,
            descending=False,
            wrap=False,
        )

    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "File" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify data is present
    assert "file1" in captured.out
    assert "file2" in captured.out
    assert "Total" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_wrapped(capsys):
    """Test rank command with wrapping enabled."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=0,
            threshold=0,
            descending=False,
            wrap=True,
        )

    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "File" in captured.out
    
    # Verify data is present
    assert "file1" in captured.out
    assert "file2" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_descending(capsys):
    """Test rank command with descending sort."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=0,
            threshold=0,
            descending=True,
            wrap=False,
        )

    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "File" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify data is present
    assert "file1" in captured.out
    assert "file2" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_limit(capsys):
    """Test rank command with limit option."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=1,
            threshold=0,
            descending=False,
            wrap=False,
        )

    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "File" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify only limited data is present
    assert "file1" in captured.out
    assert "Total" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_path(capsys):
    """Test rank command with path filter that matches nothing."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path="directory1s",
            metric=metric,
            revision_index=revision_id,
            limit=0,
            threshold=0,
            descending=False,
            wrap=False,
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_path_output(capsys):
    """Test rank command with path filter that matches files."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
    mock_iterfilenames = mock.Mock(return_value=("file1", "file2"))

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve), mock.patch("wily.commands.rank.iter_filenames", mock_iterfilenames):
        rank(
            config=mock_config,
            path="directory1s",
            metric=metric,
            revision_index=revision_id,
            limit=0,
            threshold=0,
            descending=False,
            wrap=False,
        )

    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "File" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify data is present
    assert "file1" in captured.out
    assert "file2" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_keyerror(capsys):
    """Test rank command handles KeyError with empty data."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, empty=True, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        raised = False
        try:
            rank(
                config=mock_config,
                path=None,
                metric=metric,
                revision_index=revision_id,
                limit=0,
                threshold=0,
                descending=False,
                wrap=False,
            )
        except SystemExit:
            raised = True
    assert raised, "rank didn't raise SystemExit."
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_threshold(capsys):
    """Test rank command with threshold check."""
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        raised = False
        try:
            rank(
                config=mock_config,
                path=None,
                metric=metric,
                revision_index=revision_id,
                limit=0,
                threshold=10,
                descending=False,
                wrap=False,
            )
        except SystemExit:
            raised = True
    assert raised, "rank didn't raise SystemExit."
    captured = capsys.readouterr()
    
    # Verify table output is present
    assert "File" in captured.out
    assert "Lines of Code" in captured.out
    
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()
