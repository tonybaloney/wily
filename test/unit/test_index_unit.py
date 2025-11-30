"""Unit tests for the index command."""

from unittest import mock

from wily.commands.index import index


def get_mock_State_and_config(revs):
    """Build a mock State and a mock config for command tests."""
    revisions = []
    for rev in range(revs):
        rev_dict = {
            "revision.key": f"abcdef{rev}",
            "revision.author_name": f"Author {rev}",
            "revision.message": f"Message {rev}",
            "revision.date": rev,
        }
        mock_revision = mock.Mock(**rev_dict)
        revisions.append(mock_revision)
    mock_revisions = mock.Mock(revisions=revisions)
    mock_state = mock.Mock(index={"git": mock_revisions}, archivers=("git",))
    mock.seal(mock_state)
    mock_State = mock.Mock(return_value=mock_state)
    mock_config = mock.Mock(path="", archiver="", operator="")
    return mock_State, mock_config


def test_index_without_message(capsys):
    """Test index command outputs expected data without message."""
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
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

    mock_State.assert_called_once_with(config=mock_config)


def test_index_without_message_wrapped(capsys):
    """Test index command with wrapping enabled."""
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
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

    mock_State.assert_called_once_with(config=mock_config)


def test_index_with_message(capsys):
    """Test index command with message column included."""
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
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

    mock_State.assert_called_once_with(config=mock_config)


def test_index_with_message_wrapped(capsys):
    """Test index command with message column and wrapping."""
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=True, wrap=True)

    captured = capsys.readouterr()

    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Message" in captured.out

    # Verify data is present
    assert "abcdef0" in captured.out

    mock_State.assert_called_once_with(config=mock_config)


def test_empty_index_without_message(capsys):
    """Test index command with empty data."""
    mock_State, mock_config = get_mock_State_and_config(0)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=False)

    captured = capsys.readouterr()

    # Verify table headers are present (empty table still has headers)
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out

    mock_State.assert_called_once_with(config=mock_config)


def test_empty_index_with_message(capsys):
    """Test index command with empty data and message column."""
    mock_State, mock_config = get_mock_State_and_config(0)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=True)

    captured = capsys.readouterr()

    # Verify table headers are present (empty table still has headers)
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Message" in captured.out
    assert "Date" in captured.out

    mock_State.assert_called_once_with(config=mock_config)
