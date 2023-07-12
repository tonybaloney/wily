"""Unit tests for the index command."""
from io import StringIO
from unittest import mock

from wily.commands.report import report
from wily.config import DEFAULT_GRID_STYLE
from wily.helper.custom_enums import ReportFormat


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
    mock_revisions = mock.Mock(revisions=revisions)
    mock_state = mock.Mock(index={"git": mock_revisions}, archivers=("git",))
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
    revisions.append(mock_revision)


EXPECTED = """
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ 1969-12-31 │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ 1969-12-31 │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ 1969-12-31 │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 4 (\u001b[33m+1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (0)           │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (0)           │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_report_no_message():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    assert stdout.getvalue() == EXPECTED
    mock_State.assert_called_once_with(mock_config)


EXPECTED_CHANGES_ONLY = """
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ 1969-12-31 │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ 1969-12-31 │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ 1969-12-31 │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 4 (\u001b[33m+1\u001b[0m)          │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_CHANGES_ONLY = EXPECTED_CHANGES_ONLY[1:]


def test_report_no_message_changes_only():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=True,
        )
    assert stdout.getvalue() == EXPECTED_CHANGES_ONLY
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_MESSAGE = """
╒════════════╤═══════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Message       │ Author         │ Date       │ Lines of Code   │
╞════════════╪═══════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Message 0     │ Author 0       │ 1969-12-31 │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Message 1     │ Author 1       │ 1969-12-31 │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Message 2     │ Author 2       │ 1969-12-31 │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ 1969-12-31 │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ 1969-12-31 │ 4 (\u001b[33m+1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ 1969-12-31 │ 3 (0)           │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ 1969-12-31 │ 3 (0)           │
╘════════════╧═══════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_WITH_MESSAGE = EXPECTED_WITH_MESSAGE[1:]


def test_report_with_message():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=True,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    assert stdout.getvalue() == EXPECTED_WITH_MESSAGE
    mock_State.assert_called_once_with(mock_config)


EXPECTED_EMPTY = """
╒════════════╤══════════╤════════╤═════════════════╕
│ Revision   │ Author   │ Date   │ Lines of Code   │
╞════════════╪══════════╪════════╪═════════════════╡
╘════════════╧══════════╧════════╧═════════════════╛
"""
EXPECTED_EMPTY = EXPECTED_EMPTY[1:]


def test_empty_report_no_message():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3, empty=True)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    assert stdout.getvalue() == EXPECTED_EMPTY
    mock_State.assert_called_once_with(mock_config)


EXPECTED_EMPTY_WITH_MESSAGE = """
╒════════════╤═══════════╤══════════╤════════╤═════════════════╕
│ Revision   │ Message   │ Author   │ Date   │ Lines of Code   │
╞════════════╪═══════════╪══════════╪════════╪═════════════════╡
╘════════════╧═══════════╧══════════╧════════╧═════════════════╛
"""
EXPECTED_EMPTY_WITH_MESSAGE = EXPECTED_EMPTY_WITH_MESSAGE[1:]


def test_empty_report_with_message():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    output = StringIO()
    mock_State, mock_config = get_mock_State_and_config(3, empty=True)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=True,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    assert stdout.getvalue() == EXPECTED_EMPTY_WITH_MESSAGE
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_KEYERROR = """
╒════════════╤════════════════╤════════════╤══════════════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code            │
╞════════════╪════════════════╪════════════╪══════════════════════════╡
│ abcdef0    │ Author 0       │ 1969-12-31 │ 0 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdef1    │ Author 1       │ 1969-12-31 │ 1 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdef2    │ Author 2       │ 1969-12-31 │ 2 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 4 (\u001b[33m+1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (0)                    │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ Not found 'some_path.py' │
╘════════════╧════════════════╧════════════╧══════════════════════════╛
"""
EXPECTED_WITH_KEYERROR = EXPECTED_WITH_KEYERROR[1:]


def test_report_with_keyerror():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3, with_keyerror=True)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    assert stdout.getvalue() == EXPECTED_WITH_KEYERROR
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_KEYERROR_CHANGES_ONLY = """
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ 1969-12-31 │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ 1969-12-31 │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ 1969-12-31 │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ 1969-12-31 │ 4 (\u001b[33m+1\u001b[0m)          │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_WITH_KEYERROR_CHANGES_ONLY = EXPECTED_WITH_KEYERROR_CHANGES_ONLY[1:]


def test_report_with_keyerror_changes_only():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "CONSOLE"
    mock_State, mock_config = get_mock_State_and_config(3, with_keyerror=True)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=None,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=True,
        )
    assert stdout.getvalue() == EXPECTED_WITH_KEYERROR_CHANGES_ONLY
    mock_State.assert_called_once_with(mock_config)
