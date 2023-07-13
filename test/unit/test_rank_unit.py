"""Unit tests for the index command."""

from io import StringIO
from unittest import mock

from util import get_mock_State_and_config

from wily.commands.rank import rank

EXPECTED = """
╒════════╤═════════════════╕
│ File   │   Lines of Code │
╞════════╪═════════════════╡
│ file1  │               3 │
├────────┼─────────────────┤
│ file2  │               3 │
├────────┼─────────────────┤
│ Total  │               6 │
╘════════╧═════════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_rank():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_find = mock.Mock()
    mock_find.find = mock.Mock(return_value=mock_revision)
    mock_cls = mock.Mock()
    mock_cls.cls = mock.Mock(return_value=mock_find)
    mock_resolve = mock.MagicMock(return_value=mock_cls)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=None,
            threshold=None,
            descending=False,
        )

    assert stdout.getvalue() == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()
    mock_cls.cls.assert_called_once()
    mock_find.find.assert_called_once()


def test_keyerror():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, empty=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_find = mock.Mock()
    mock_find.find = mock.Mock(return_value=mock_revision)
    mock_cls = mock.Mock()
    mock_cls.cls = mock.Mock(return_value=mock_find)
    mock_resolve = mock.MagicMock(return_value=mock_cls)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        raised = False
        try:
            rank(
                config=mock_config,
                path=None,
                metric=metric,
                revision_index=revision_id,
                limit=None,
                threshold=None,
                descending=False,
            )
        except SystemExit:
            raised = True
    assert raised, "rank didn't raise SystemExit."
    assert stdout.getvalue() == ""
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()
    mock_cls.cls.assert_called_once()
    mock_find.find.assert_called_once()


def test_threshold():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_find = mock.Mock()
    mock_find.find = mock.Mock(return_value=mock_revision)
    mock_cls = mock.Mock()
    mock_cls.cls = mock.Mock(return_value=mock_find)
    mock_resolve = mock.MagicMock(return_value=mock_cls)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        raised = False
        try:
            rank(
                config=mock_config,
                path=None,
                metric=metric,
                revision_index=revision_id,
                limit=None,
                threshold=10,
                descending=False,
            )
        except SystemExit:
            raised = True
    assert raised, "rank didn't raise SystemExit."
    assert stdout.getvalue() == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()
    mock_cls.cls.assert_called_once()
    mock_find.find.assert_called_once()
