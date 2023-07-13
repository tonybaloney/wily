"""Unit tests for the index command."""

from io import StringIO
from unittest import mock

from util import get_mock_State_and_config

from wily.commands.report import report
from wily.config import DEFAULT_GRID_STYLE
from wily.helper.custom_enums import ReportFormat

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


EXPECTED_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>wily report</title>
    <link rel="stylesheet" href="css/main.css" type="text/css">
</head>
<body class="indexfile">
    <div class="limiter">
		<div class="container-table100">
			<div class="wrap-table100">
                <table class="index">
                    <thead>
                        <tr><th>Revision</th><th>Author</th><th>Date</th><th>Lines of Code</th></tr>
                    </thead>
                    <tbody>
"""
EXPECTED_HTML += (
    "                        <tr><td>abcdef0</td><td>Author 0</td><td>1969-12-31</td><td>0 (<span class='orange-color'>-1</span>)</td></tr>"
    "<tr><td>abcdef1</td><td>Author 1</td><td>1969-12-31</td><td>1 (<span class='orange-color'>-1</span>)</td></tr>"
    "<tr><td>abcdef2</td><td>Author 2</td><td>1969-12-31</td><td>2 (<span class='orange-color'>-1</span>)</td></tr>"
    "<tr><td>abcdeff</td><td>Author Someone</td><td>1969-12-31</td><td>3 (<span class='orange-color'>-1</span>)</td></tr>"
    "<tr><td>abcdeff</td><td>Author Someone</td><td>1969-12-31</td><td>4 (<span class='orange-color'>+1</span>)</td></tr>"
    "<tr><td>abcdeff</td><td>Author Someone</td><td>1969-12-31</td><td>3 (0)</td></tr>"
    "<tr><td>abcdeff</td><td>Author Someone</td><td>1969-12-31</td><td>Not found 'some_path.py'</td></tr>"
)
EXPECTED_HTML += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""


def test_report_html():
    path = "test.py"
    metrics = ("raw.loc",)
    format = "HTML"

    mock_output, output = get_outputs()

    mock_State, mock_config = get_mock_State_and_config(3, with_keyerror=True)
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout), mock.patch(
        "wily.commands.report.State", mock_State
    ), mock.patch("wily.commands.report.copytree"):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=mock_output,
            include_message=False,
            format=ReportFormat[format],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )

    assert output.getvalue() == EXPECTED_HTML
    mock_State.assert_called_once_with(mock_config)


def get_outputs():
    output = StringIO()
    enter = mock.MagicMock(return_value=output)
    writer = mock.MagicMock(__enter__=enter)
    opener = mock.MagicMock(return_value=writer)
    mock_output = mock.MagicMock(
        is_file=True, suffix=".html", parents=[mock.MagicMock()], open=opener
    )
    return mock_output, output
