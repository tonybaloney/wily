"""Utils for unit testing wily."""
from unittest import mock


def get_mock_State_and_config(revs, empty=False, with_keyerror=False):
    """Build a mock State and a mock config for command tests."""
    revisions = []
    if not empty:
        for rev in range(revs):
            add_revision(rev, revisions)
        rev_dict = {
            "key": "abcdeff",
            "author": "Author Someone",
            "message": "Message here.",
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
    """Add a mock revision to the revisions list."""
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
