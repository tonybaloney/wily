"""
Parameterised tests for each operator (and some combinations).

Build them and test out some of the metrics/commands work correctly.
"""
import pytest
from click.testing import CliRunner

import wily.__main__ as main

operators = (
    'halstead',
    'cyclomatic',
    'maintainability',
    'raw',
    'halstead,cyclomatic',
    'maintainability,raw',
    'halstead,cyclomatic,maintainability,raw'
)

@pytest.mark.parametrize("operator", operators)
def test_operator(operator, gitdir):
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "build", "src", "-o", operator]
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "report", "src/test.py"]
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(
        main.cli, ["--debug", "--path", gitdir, "diff", "src/test.py", "--all"]
    )
    assert result.exit_code == 0, result.stdout