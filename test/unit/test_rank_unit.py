"""Unit tests for the index command."""

from io import StringIO
from unittest import mock

from util import get_mock_State_and_config

from wily.commands.rank import rank

EXPECTED = """
╒════════╤═════════════════╕
│ File   │   Lines of Code │
╞════════╪═════════════════╡
│ file1  │               0 │
├────────┼─────────────────┤
│ file2  │               1 │
├────────┼─────────────────┤
│ Total  │               1 │
╘════════╧═════════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_rank():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
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


EXPECTED_DESCENDING = """
╒════════╤═════════════════╕
│ File   │   Lines of Code │
╞════════╪═════════════════╡
│ file2  │               1 │
├────────┼─────────────────┤
│ file1  │               0 │
├────────┼─────────────────┤
│ Total  │               1 │
╘════════╧═════════════════╛
"""
EXPECTED_DESCENDING = EXPECTED_DESCENDING[1:]


def test_rank_descending():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
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
            descending=True,
        )

    assert stdout.getvalue() == EXPECTED_DESCENDING
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


EXPECTED_LIMIT = """
╒════════╤═════════════════╕
│ File   │   Lines of Code │
╞════════╪═════════════════╡
│ file1  │               0 │
├────────┼─────────────────┤
│ Total  │               0 │
╘════════╧═════════════════╛
"""
EXPECTED_LIMIT = EXPECTED_LIMIT[1:]


def test_rank_limit():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path=None,
            metric=metric,
            revision_index=revision_id,
            limit=1,
            threshold=None,
            descending=False,
        )

    assert stdout.getvalue() == EXPECTED_LIMIT
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_path():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve):
        rank(
            config=mock_config,
            path="directory1s",
            metric=metric,
            revision_index=revision_id,
            limit=None,
            threshold=None,
            descending=False,
        )

    assert stdout.getvalue() == ""
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_path_output():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
    mock_iterfilenames = mock.Mock(return_value=("file1", "file2"))
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.rank.State", mock_State
    ), mock.patch("wily.commands.rank.resolve_archiver", mock_resolve), mock.patch(
        "radon.cli.harvest.iter_filenames", mock_iterfilenames
    ):
        rank(
            config=mock_config,
            path="directory1s",
            metric=metric,
            revision_index=revision_id,
            limit=None,
            threshold=None,
            descending=False,
        )

    assert stdout.getvalue() == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_keyerror():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, empty=True, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
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


def test_threshold():
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_State_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
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
