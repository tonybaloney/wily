"""Unit tests for the index command."""
from io import StringIO
from unittest import mock

from wily.commands.rank import rank


def get_mock_State_and_config(revs, empty=False, with_keyerror=False):
    revisions = []
    if not empty:
        for rev in range(revs):
            add_revision(rev, revisions)
        rev_dict = {
            "key": f"abcdeff",
            "author": f"Author Someone",
            "message": f"Message here.",
            "date": 10,
        }
        add_revision(revs, revisions, val=revs, **rev_dict)
        add_revision(revs, revisions, val=revs + 1, **rev_dict)
        add_revision(revs, revisions, val=revs, **rev_dict)
        add_revision(revs, revisions, val=revs, **rev_dict, with_keyerror=with_keyerror)
    if revisions:
        mock__get_item__ = mock.Mock(return_value=revisions[-1])
    else:
        mock__get_item__ = mock.Mock(side_effect=KeyError)

    mock_revisions = mock.MagicMock(revisions=revisions, __getitem__=mock__get_item__)
    mock_state = mock.Mock(
        index={"git": mock_revisions}, archivers=("git",), default_archiver="git"
    )
    mock.seal(mock_state)
    mock_State = mock.Mock(return_value=mock_state)
    mock_config = mock.Mock(path="", archiver="", operator="")
    return mock_State, mock_config


def add_revision(
    rev,
    revisions,
    key=None,
    author=None,
    message=None,
    date=None,
    val=None,
    with_keyerror=False,
):
    rev_dict = {
        "revision.key": key or f"abcdef{rev}",
        "revision.author_name": author or f"Author {rev}",
        "revision.message": message or f"Message {rev}",
        "revision.date": date or rev,
    }
    if with_keyerror:
        mock_get = mock.Mock(side_effect=KeyError("some_path.py"))
    else:
        mock_get = mock.Mock(return_value=val or rev)
    mock_revision = mock.Mock(get=mock_get, **rev_dict)
    mock_get_paths = mock.MagicMock(return_value=("file1", "file2"))
    mock_revision.get_paths = mock_get_paths
    revisions.append(mock_revision)


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
