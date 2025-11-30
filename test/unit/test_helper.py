"""Unit tests for the helper module."""

from rich import box
from rich.text import Text

from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import generate_cache_path, get_box_style, print_table, styled_text


def test_get_box_style_default():
    """Test get_box_style returns ROUNDED by default."""
    style = get_box_style()
    assert style == box.ROUNDED


def test_get_box_style_custom():
    """Test get_box_style returns correct box style for valid names."""
    assert get_box_style("ASCII") == box.ASCII
    assert get_box_style("SIMPLE") == box.SIMPLE
    assert get_box_style("HEAVY") == box.HEAVY
    assert get_box_style("DOUBLE") == box.DOUBLE
    assert get_box_style("MINIMAL") == box.MINIMAL


def test_get_box_style_case_insensitive():
    """Test get_box_style is case-insensitive."""
    assert get_box_style("ascii") == box.ASCII
    assert get_box_style("ASCII") == box.ASCII
    assert get_box_style("Ascii") == box.ASCII


def test_get_box_style_invalid_returns_rounded():
    """Test get_box_style returns ROUNDED for invalid style names."""
    style = get_box_style("nonexistent_style")
    assert style == box.ROUNDED


def test_styled_text():
    """Test styled_text creates a Text object with correct style."""
    result = styled_text("hello", "red")
    assert isinstance(result, Text)
    assert str(result) == "hello"


def test_styled_text_green():
    """Test styled_text with green style."""
    result = styled_text("success", "green")
    assert isinstance(result, Text)
    assert str(result) == "success"


def test_styled_text_yellow():
    """Test styled_text with yellow style."""
    result = styled_text("warning", "yellow")
    assert isinstance(result, Text)
    assert str(result) == "warning"


def test_print_table(capsys):
    """Test print_table outputs a table."""
    headers = ["Col1", "Col2"]
    data = [["a", "b"], ["c", "d"]]

    print_table(headers, data, wrap=True)

    captured = capsys.readouterr()
    assert "Col1" in captured.out
    assert "Col2" in captured.out
    assert "a" in captured.out
    assert "b" in captured.out
    assert "c" in captured.out
    assert "d" in captured.out


def test_print_table_with_text_objects(capsys):
    """Test print_table handles Rich Text objects."""
    headers = ["Name", "Status"]
    data = [
        ["test1", styled_text("pass", "green")],
        ["test2", styled_text("fail", "red")],
    ]

    print_table(headers, data, wrap=True)

    captured = capsys.readouterr()
    assert "Name" in captured.out
    assert "Status" in captured.out
    assert "test1" in captured.out
    assert "test2" in captured.out
    assert "pass" in captured.out
    assert "fail" in captured.out


def test_print_table_with_style(capsys):
    """Test print_table uses the specified box style."""
    headers = ["A", "B"]
    data = [["1", "2"]]

    # Should not raise an error with different styles
    print_table(headers, data, wrap=True, table_style="ASCII")
    captured = capsys.readouterr()
    assert "A" in captured.out

    print_table(headers, data, wrap=True, table_style="SIMPLE")
    captured = capsys.readouterr()
    assert "A" in captured.out


def test_generate_cache_path():
    """Test generate_cache_path returns a consistent path."""
    path1 = generate_cache_path("/some/path")
    path2 = generate_cache_path("/some/path")
    assert path1 == path2
    assert ".wily" in path1


def test_generate_cache_path_different_paths():
    """Test generate_cache_path returns different paths for different inputs."""
    path1 = generate_cache_path("/path/one")
    path2 = generate_cache_path("/path/two")
    assert path1 != path2


def test_default_table_style_constant():
    """Test that DEFAULT_TABLE_STYLE is set correctly."""
    assert DEFAULT_TABLE_STYLE == "ROUNDED"
