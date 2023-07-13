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


EXPECTED = """
╒════════════╤══════════╤════════════╕
│ Revision   │ Author   │ Date       │
╞════════════╪══════════╪════════════╡
│ abcdef0    │ Author 0 │ 1969-12-31 │
├────────────┼──────────┼────────────┤
│ abcdef1    │ Author 1 │ 1969-12-31 │
├────────────┼──────────┼────────────┤
│ abcdef2    │ Author 2 │ 1969-12-31 │
╘════════════╧══════════╧════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_index_without_message(capsys):
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=False)

    captured = capsys.readouterr()
    assert captured.out == EXPECTED
    mock_State.assert_called_once_with(config=mock_config)


EXPECTED_WITH_MESSAGE = """
╒════════════╤══════════╤═══════════╤════════════╕
│ Revision   │ Author   │ Message   │ Date       │
╞════════════╪══════════╪═══════════╪════════════╡
│ abcdef0    │ Author 0 │ Message 0 │ 1969-12-31 │
├────────────┼──────────┼───────────┼────────────┤
│ abcdef1    │ Author 1 │ Message 1 │ 1969-12-31 │
├────────────┼──────────┼───────────┼────────────┤
│ abcdef2    │ Author 2 │ Message 2 │ 1969-12-31 │
╘════════════╧══════════╧═══════════╧════════════╛
"""
EXPECTED_WITH_MESSAGE = EXPECTED_WITH_MESSAGE[1:]


def test_index_with_message(capsys):
    mock_State, mock_config = get_mock_State_and_config(3)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=True)

    captured = capsys.readouterr()
    assert captured.out == EXPECTED_WITH_MESSAGE
    mock_State.assert_called_once_with(config=mock_config)


EXPECTED_EMPTY = """
╒════════════╤══════════╤════════╕
│ Revision   │ Author   │ Date   │
╞════════════╪══════════╪════════╡
╘════════════╧══════════╧════════╛
"""
EXPECTED_EMPTY = EXPECTED_EMPTY[1:]


def test_empty_index_without_message(capsys):
    mock_State, mock_config = get_mock_State_and_config(0)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=False)

    captured = capsys.readouterr()
    assert captured.out == EXPECTED_EMPTY
    mock_State.assert_called_once_with(config=mock_config)


EXPECTED_EMPTY_WITH_MESSAGE = """
╒════════════╤══════════╤═══════════╤════════╕
│ Revision   │ Author   │ Message   │ Date   │
╞════════════╪══════════╪═══════════╪════════╡
╘════════════╧══════════╧═══════════╧════════╛
"""
EXPECTED_EMPTY_WITH_MESSAGE = EXPECTED_EMPTY_WITH_MESSAGE[1:]


def test_empty_index_with_message(capsys):
    mock_State, mock_config = get_mock_State_and_config(0)

    with mock.patch("wily.commands.index.State", mock_State):
        index(mock_config, include_message=True)

    captured = capsys.readouterr()
    assert captured.out == EXPECTED_EMPTY_WITH_MESSAGE
    mock_State.assert_called_once_with(config=mock_config)
