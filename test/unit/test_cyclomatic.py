"""
Tests for the cyclomatic complexity operator's ability to handle bad data.
"""
from unittest import mock

import wily.operators.cyclomatic
from wily.config import DEFAULT_CONFIG


@mock.patch("wily.operators.cyclomatic.iter_filenames", return_value=["test.py"])
@mock.patch("builtins.open", mock.mock_open(read_data="def foo(): pass"))
@mock.patch("wily.operators.cyclomatic.harvest_cyclomatic_metrics")
def test_cyclomatic_parse_error(mock_harvest, mock_iter):
    """Test handling of parse errors from Rust backend."""
    mock_harvest.return_value = [("test.py", {"error": "parse error"})]
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results == {"test.py": {"detailed": {}, "total": {"complexity": 0}}}


@mock.patch("wily.operators.cyclomatic.iter_filenames", return_value=["test.py"])
@mock.patch("builtins.open", mock.mock_open(read_data="def foo(): pass"))
@mock.patch("wily.operators.cyclomatic.harvest_cyclomatic_metrics")
def test_cyclomatic_empty_results(mock_harvest, mock_iter):
    """Test handling of empty results from Rust backend."""
    mock_harvest.return_value = [("test.py", {"functions": [], "classes": []})]
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results == {"test.py": {"detailed": {}, "total": {"complexity": 0}}}


@mock.patch("wily.operators.cyclomatic.iter_filenames", return_value=["test.py"])
@mock.patch("builtins.open", side_effect=IOError("file not found"))
def test_cyclomatic_file_read_error(mock_open, mock_iter):
    """Test handling of file read errors."""
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert "error" in results["test.py"]["total"]


@mock.patch("wily.operators.cyclomatic.iter_filenames", return_value=["test.py"])
@mock.patch("builtins.open", mock.mock_open(read_data="def foo():\n    if x:\n        return 1\n    return 0"))
@mock.patch("wily.operators.cyclomatic.harvest_cyclomatic_metrics")
def test_cyclomatic_function_result(mock_harvest, mock_iter):
    """Test processing of function results from Rust backend."""
    mock_harvest.return_value = [("test.py", {
        "functions": [{
            "name": "foo",
            "fullname": "foo",
            "lineno": 1,
            "endline": 4,
            "complexity": 2,
            "is_method": False,
            "classname": None,
            "closures": [],
        }],
        "classes": []
    })]
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results["test.py"]["total"]["complexity"] == 2
    assert "foo" in results["test.py"]["detailed"]
    assert results["test.py"]["detailed"]["foo"]["complexity"] == 2
