"""
Tests for the cyclomatic complexity operator's ability to handle bad data from radon.
"""
import mock
import wily.operators.cyclomatic
from wily.config import DEFAULT_CONFIG


class MockCC(object):
    results = {}


@mock.patch("wily.operators.cyclomatic.harvesters.CCHarvester", return_value=MockCC)
def test_cyclomatic_bad_entry_data(harvester):
    MockCC.results = {"test.py": [{"complexity": 5}]}
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results == {"test.py": {"detailed": {}, "total": {"complexity": 0}}}


@mock.patch("wily.operators.cyclomatic.harvesters.CCHarvester", return_value=MockCC)
def test_cyclomatic_error_case(harvester):
    MockCC.results = {"test.py": {"error": "bad data"}}
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results == {"test.py": {"detailed": {}, "total": {"complexity": 0}}}


@mock.patch("wily.operators.cyclomatic.harvesters.CCHarvester", return_value=MockCC)
def test_cyclomatic_error_case_unexpected(harvester):
    MockCC.results = {"test.py": [1234]}
    op = wily.operators.cyclomatic.CyclomaticComplexityOperator(DEFAULT_CONFIG, ["."])
    results = op.run("test.py", {})
    assert results == {"test.py": {"detailed": {}, "total": {"complexity": 0}}}
