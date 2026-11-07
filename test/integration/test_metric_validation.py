"""
Unknown or malformed metric names must produce a click usage error, not a traceback.

Regression tests for https://github.com/tonybaloney/wily/issues/285
"""

import pytest
from click.testing import CliRunner

import wily.__main__ as main

_path = "src/test.py"

INVALID_INVOCATIONS = [
    # The original report: "--help" is consumed as the value of -m.
    pytest.param(["graph", _path, "-m", "--help"], "is not a metric name", id="graph-m-help"),
    pytest.param(["graph", _path, "-m", "foo"], "Unknown metric 'foo'", id="graph-unknown"),
    pytest.param(["graph", _path, "-m", "raw.loc,foo"], "Unknown metric 'foo'", id="graph-second-unknown"),
    pytest.param(["graph", _path, "-m", "raw.loc,"], "Empty metric name", id="graph-trailing-comma"),
    pytest.param(["graph", _path, "-m", "bogus.loc"], "Unknown operator 'bogus'", id="graph-unknown-operator"),
    pytest.param(["graph", _path, "-m", "raw.loc.extra"], "operator.metric", id="graph-too-many-dots"),
    pytest.param(["graph", _path, "-m", "raw.loc", "-x", "foo"], "Unknown metric 'foo'", id="graph-x-axis-unknown"),
    pytest.param(["report", _path, "foo"], "Unknown metric 'foo'", id="report-unknown"),
    pytest.param(["report", _path, "raw.loc", "foo"], "Unknown metric 'foo'", id="report-second-unknown"),
    pytest.param(["rank", "src/", "foo"], "Unknown metric 'foo'", id="rank-unknown"),
    pytest.param(["diff", _path, "-m", "foo"], "operator.metric", id="diff-missing-operator"),
    pytest.param(["diff", _path, "-m", "bogus.loc"], "Unknown operator 'bogus'", id="diff-unknown-operator"),
    pytest.param(["diff", _path, "-m", "raw.foo"], "Unknown metric 'raw.foo'", id="diff-unknown-metric"),
]


@pytest.mark.parametrize(("args", "message"), INVALID_INVOCATIONS)
def test_invalid_metric_is_usage_error(builddir, args, message):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, *args])
    assert result.exit_code == 2, result.output  # click usage error, not an uncaught exception (exit 1)
    assert isinstance(result.exception, SystemExit), result.exception
    assert "Traceback" not in result.output
    assert "Invalid value" in result.output
    assert message in result.output
    assert "wily list-metrics" in result.output


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(["graph", _path, "-m", "raw.loc,cyclomatic.complexity", "-x", "raw.sloc", "-o", "{out}"], id="graph"),
        pytest.param(["report", _path, "raw.loc", "loc"], id="report-with-and-without-operator"),
        pytest.param(["rank", "src/", "raw.loc"], id="rank"),
        pytest.param(["diff", _path, "-m", "raw.loc,maintainability.mi"], id="diff"),
    ],
)
def test_valid_metrics_still_accepted(builddir, tmp_path, args):
    # Write graphs to a file so no browser is opened.
    args = [a.format(out=tmp_path / "graph.html") for a in args]
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, *args])
    assert result.exit_code == 0, result.output
