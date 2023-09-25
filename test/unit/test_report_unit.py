"""Unit tests for the report command."""

from io import StringIO
from pathlib import Path
from unittest import mock

from util import get_mock_state_and_config

from wily import format_date as fd
from wily.commands.report import report
from wily.defaults import DEFAULT_GRID_STYLE
from wily.helper.custom_enums import ReportFormat

EXPECTED = f"""
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ {fd(0)} │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ {fd(1)} │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ {fd(2)} │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 4 (\u001b[33m+1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (0)           │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (0)           │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_report_no_message(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == EXPECTED
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WRAPPED = f"""
╒══════════╤══════════╤════════╤═════════╕
│ Revisi   │ Author   │ Date   │ Lines   │
│ on       │          │        │ of      │
│          │          │        │ Code    │
╞══════════╪══════════╪════════╪═════════╡
│ abcdef   │ Author   │ {fd(0)[:6]} │ 0 (\u001b[33m-1\u001b[0m)  │
│ 0        │ 0        │ {fd(0)[6:]:<6} │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(1)[:6]} │ 1 (\u001b[33m-1\u001b[0m)  │
│ 1        │ 1        │ {fd(1)[6:]:<6} │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(2)[:6]} │ 2 (\u001b[33m-1\u001b[0m)  │
│ 2        │ 2        │ {fd(2)[6:]:<6} │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(3)[:6]} │ 3 (\u001b[33m-1\u001b[0m)  │
│ f        │ Someon   │ {fd(3)[6:]:<6} │         │
│          │ e        │        │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(4)[:6]} │ 4 (\u001b[33m+1\u001b[0m)  │
│ f        │ Someon   │ {fd(4)[6:]:<6} │         │
│          │ e        │        │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(5)[:6]} │ 3 (0)   │
│ f        │ Someon   │ {fd(5)[6:]:<6} │         │
│          │ e        │        │         │
├──────────┼──────────┼────────┼─────────┤
│ abcdef   │ Author   │ {fd(6)[:6]} │ 3 (0)   │
│ f        │ Someon   │ {fd(6)[6:]:<6} │         │
│          │ e        │        │         │
╘══════════╧══════════╧════════╧═════════╛
"""
EXPECTED_WRAPPED = EXPECTED_WRAPPED[1:]


def test_report_no_message_wrapped(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3)

    mock_get_terminal_size = mock.Mock(return_value=(50, 24))
    mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

    with mock.patch("wily.commands.report.State", mock_State), mock.patch(
        "wily.helper.shutil", mock_shutil
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
            wrap=True,
        )
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == EXPECTED_WRAPPED
    mock_State.assert_called_once_with(mock_config)


EXPECTED_CHANGES_ONLY = f"""
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ {fd(0)} │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ {fd(1)} │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ {fd(2)} │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 4 (\u001b[33m+1\u001b[0m)          │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_CHANGES_ONLY = EXPECTED_CHANGES_ONLY[1:]


def test_report_no_message_changes_only(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=True,
        )
    captured = capsys.readouterr()
    assert captured.out == EXPECTED_CHANGES_ONLY
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_MESSAGE = f"""
╒════════════╤═══════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Message       │ Author         │ Date       │ Lines of Code   │
╞════════════╪═══════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Message 0     │ Author 0       │ {fd(0)} │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Message 1     │ Author 1       │ {fd(1)} │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Message 2     │ Author 2       │ {fd(2)} │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ {fd(3)} │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ {fd(10)} │ 4 (\u001b[33m+1\u001b[0m)          │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ {fd(10)} │ 3 (0)           │
├────────────┼───────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Message here. │ Author Someone │ {fd(10)} │ 3 (0)           │
╘════════════╧═══════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_WITH_MESSAGE = EXPECTED_WITH_MESSAGE[1:]


def test_report_with_message(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=True,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == EXPECTED_WITH_MESSAGE
    mock_State.assert_called_once_with(mock_config)


def test_empty_report_no_message(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3, empty=True)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)


def test_empty_report_with_message(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3, empty=True)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=True,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_KEYERROR = f"""
╒════════════╤════════════════╤════════════╤══════════════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code            │
╞════════════╪════════════════╪════════════╪══════════════════════════╡
│ abcdef0    │ Author 0       │ {fd(0)} │ 0 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdef1    │ Author 1       │ {fd(1)} │ 1 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdef2    │ Author 2       │ {fd(2)} │ 2 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ {fd(3)} │ 3 (\u001b[33m-1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 4 (\u001b[33m+1\u001b[0m)                   │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (0)                    │
├────────────┼────────────────┼────────────┼──────────────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ Not found 'some_path.py' │
╘════════════╧════════════════╧════════════╧══════════════════════════╛
"""
EXPECTED_WITH_KEYERROR = EXPECTED_WITH_KEYERROR[1:]


def test_report_with_keyerror(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3, with_keyerror=True)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == EXPECTED_WITH_KEYERROR
    mock_State.assert_called_once_with(mock_config)


EXPECTED_WITH_KEYERROR_CHANGES_ONLY = f"""
╒════════════╤════════════════╤════════════╤═════════════════╕
│ Revision   │ Author         │ Date       │ Lines of Code   │
╞════════════╪════════════════╪════════════╪═════════════════╡
│ abcdef0    │ Author 0       │ {fd(0)} │ 0 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef1    │ Author 1       │ {fd(1)} │ 1 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdef2    │ Author 2       │ {fd(2)} │ 2 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 3 (\u001b[33m-1\u001b[0m)          │
├────────────┼────────────────┼────────────┼─────────────────┤
│ abcdeff    │ Author Someone │ {fd(10)} │ 4 (\u001b[33m+1\u001b[0m)          │
╘════════════╧════════════════╧════════════╧═════════════════╛
"""
EXPECTED_WITH_KEYERROR_CHANGES_ONLY = EXPECTED_WITH_KEYERROR_CHANGES_ONLY[1:]


def test_report_with_keyerror_changes_only(capsys):
    path = "test.py"
    metrics = ("raw.loc",)
    format_ = "CONSOLE"
    mock_State, mock_config = get_mock_state_and_config(3, with_keyerror=True)

    with mock.patch("wily.commands.report.State", mock_State):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=Path(),
            include_message=False,
            format=ReportFormat[format_],
            console_format=DEFAULT_GRID_STYLE,
            changes_only=True,
        )
    captured = capsys.readouterr()
    assert captured.out == EXPECTED_WITH_KEYERROR_CHANGES_ONLY
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
    f"                        <tr><td>abcdef0</td><td>Author 0</td><td>{fd(0)}</td><td>0 (<span class='orange-color'>-1</span>)</td></tr>"
    f"<tr><td>abcdef1</td><td>Author 1</td><td>{fd(1)}</td><td>1 (<span class='orange-color'>-1</span>)</td></tr>"
    f"<tr><td>abcdef2</td><td>Author 2</td><td>{fd(2)}</td><td>2 (<span class='orange-color'>-1</span>)</td></tr>"
    f"<tr><td>abcdeff</td><td>Author Someone</td><td>{fd(10)}</td><td>3 (<span class='orange-color'>-1</span>)</td></tr>"
    f"<tr><td>abcdeff</td><td>Author Someone</td><td>{fd(10)}</td><td>4 (<span class='orange-color'>+1</span>)</td></tr>"
    f"<tr><td>abcdeff</td><td>Author Someone</td><td>{fd(10)}</td><td>3 (0)</td></tr>"
    f"<tr><td>abcdeff</td><td>Author Someone</td><td>{fd(10)}</td><td>Not found 'some_path.py'</td></tr>"
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
    format_ = "HTML"

    mock_output, output = get_outputs()

    mock_State, mock_config = get_mock_state_and_config(3, with_keyerror=True)

    with mock.patch("wily.commands.report.State", mock_State), mock.patch(
        "wily.commands.report.copytree"
    ):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=mock_output,
            include_message=False,
            format=ReportFormat[format_],
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
