"""Unit tests for the report command."""

from io import StringIO
from pathlib import Path
from unittest import mock

from util import get_mock_state_and_config

from wily import format_date as fd
from wily.commands.report import report
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper.custom_enums import ReportFormat


def test_report_no_message(capsys):
    """Test report command outputs expected data without message."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify data is present
    assert "abcdef0" in captured.out
    assert "Author 0" in captured.out
    assert "abcdef1" in captured.out
    assert "abcdef2" in captured.out
    assert "abcdeff" in captured.out
    assert "Author Someone" in captured.out
    
    mock_State.assert_called_once_with(mock_config)


def test_report_no_message_wrapped(capsys):
    """Test report command with wrapping enabled."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
            wrap=True,
        )
    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Date" in captured.out
    
    # Verify data is present
    assert "abcdef0" in captured.out
    assert "abcdef1" in captured.out
    assert "abcdef2" in captured.out
    
    mock_State.assert_called_once_with(mock_config)


def test_report_no_message_changes_only(capsys):
    """Test report command with changes_only filter."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=True,
        )
    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Author" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify data without changes is filtered (rows with 0 delta should be excluded)
    assert "abcdef0" in captured.out
    
    mock_State.assert_called_once_with(mock_config)


def test_report_with_message(capsys):
    """Test report command with message column included."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    
    # Verify table headers include Message
    assert "Revision" in captured.out
    assert "Message" in captured.out
    assert "Author" in captured.out
    
    # Verify message data is present
    assert "Message 0" in captured.out or "Message here" in captured.out
    
    mock_State.assert_called_once_with(mock_config)


def test_empty_report_no_message(capsys):
    """Test report command with empty data."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)


def test_empty_report_with_message(capsys):
    """Test report command with empty data and message column."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_State.assert_called_once_with(mock_config)


def test_report_with_keyerror(capsys):
    """Test report command handles KeyError for missing files."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )
    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Lines of Code" in captured.out
    
    # Verify "Not found" message is present for missing file
    assert "Not found" in captured.out
    
    mock_State.assert_called_once_with(mock_config)


def test_report_with_keyerror_changes_only(capsys):
    """Test report command handles KeyError with changes_only filter."""
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
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=True,
        )
    captured = capsys.readouterr()
    
    # Verify table headers are present
    assert "Revision" in captured.out
    assert "Lines of Code" in captured.out
    
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

    with mock.patch("wily.commands.report.State", mock_State), mock.patch("wily.commands.report.copytree"):
        report(
            config=mock_config,
            path=path,
            metrics=metrics,
            n=10,
            output=mock_output,
            include_message=False,
            format=ReportFormat[format_],
            table_style=DEFAULT_TABLE_STYLE,
            changes_only=False,
        )

    assert output.getvalue() == EXPECTED_HTML
    mock_State.assert_called_once_with(mock_config)


def get_outputs():
    output = StringIO()
    enter = mock.MagicMock(return_value=output)
    writer = mock.MagicMock(__enter__=enter)
    opener = mock.MagicMock(return_value=writer)
    mock_output = mock.MagicMock(is_file=True, suffix=".html", parents=[mock.MagicMock()], open=opener)
    return mock_output, output
