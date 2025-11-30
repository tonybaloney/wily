"""Unit tests for the list_metrics command."""

from statistics import mean
from unittest import mock

from wily.commands.list_metrics import list_metrics


def test_list_metrics_no_wrap(capsys):
    """Test list_metrics command outputs expected metric information."""
    list_metrics(wrap=False)
    captured = capsys.readouterr()
    
    # Verify operator headers are present
    assert "cyclomatic operator:" in captured.out
    assert "maintainability operator:" in captured.out
    assert "raw operator:" in captured.out
    assert "halstead operator:" in captured.out
    
    # Verify table headers are present
    assert "Name" in captured.out
    assert "Description" in captured.out
    assert "Type" in captured.out
    assert "Measure" in captured.out
    assert "Aggregate" in captured.out
    
    # Verify some metric data is present
    assert "complexity" in captured.out
    assert "Cyclomatic Complexity" in captured.out
    assert "mi" in captured.out
    assert "Maintainability Index" in captured.out
    assert "loc" in captured.out
    assert "Lines of Code" in captured.out


def test_list_metrics_wrapped(capsys):
    """Test list_metrics command with wrapping enabled."""
    list_metrics(wrap=True)
    captured = capsys.readouterr()
    
    # Verify operator headers are present
    assert "cyclomatic operator:" in captured.out
    assert "maintainability operator:" in captured.out
    assert "raw operator:" in captured.out
    assert "halstead operator:" in captured.out
    
    # Verify table headers are present
    assert "Name" in captured.out
    assert "Description" in captured.out
    
    # Verify some metric data is present
    assert "complexity" in captured.out
    assert "mi" in captured.out
    assert "loc" in captured.out
