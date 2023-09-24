"""Unit tests for the rank command."""

from unittest import mock

from util import get_mock_state_and_config

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


def test_rank(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    assert captured.out == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


EXPECTED_WRAPPED = """
╒════════╤════════════╕
│ File   │   Lines of │
│        │       Code │
╞════════╪════════════╡
│ file1  │          0 │
├────────┼────────────┤
│ file2  │          1 │
├────────┼────────────┤
│ Total  │          1 │
╘════════╧════════════╛
"""
EXPECTED_WRAPPED = EXPECTED_WRAPPED[1:]


def test_rank_wrapped(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    mock_get_terminal_size = mock.Mock(return_value=(25, 24))
    mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ), mock.patch("wily.helper.shutil", mock_shutil):
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
    assert captured.out == EXPECTED_WRAPPED
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


def test_rank_descending(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    assert captured.out == EXPECTED_DESCENDING
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


def test_rank_limit(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    assert captured.out == EXPECTED_LIMIT
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_rank_path(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)
    mock_iterfilenames = mock.Mock(return_value=("file1", "file2"))

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ), mock.patch("radon.cli.harvest.iter_filenames", mock_iterfilenames):
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
    assert captured.out == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()


def test_keyerror(capsys):
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, empty=True, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    metric = "raw.loc"
    revision_id = "abcdeff"
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_revision = mock.MagicMock(key="abcdeff123123", message="Nothing.")
    mock_resolve = mock.MagicMock()
    mock_resolve.cls.find = mock.Mock(return_value=mock_revision)

    with mock.patch("wily.commands.rank.State", mock_State), mock.patch(
        "wily.commands.rank.resolve_archiver", mock_resolve
    ):
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
    assert captured.out == EXPECTED
    mock_State.assert_called_once_with(mock_config)
    mock_resolve.assert_called_once()
