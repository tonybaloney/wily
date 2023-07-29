from click.testing import CliRunner

import wily.__main__ as main


def test_list_metrics(builddir):
    """
    Test that list-metrics works and is ordered
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["list-metrics"])
    assert result.stdout.count("operator") == 4
    assert "cyclomatic" in result.stdout
    assert "maintainability" in result.stdout
    assert "raw" in result.stdout
    assert "halstead" in result.stdout
    # Test ordering
    i = result.stdout.index
    assert i("cyclomatic") < i("maintainability") < i("raw") < i("halstead")


def test_list_metrics_wrapped(builddir):
    """
    Test that list-metrics works with wrapping
    """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["list-metrics", "--wrap"])
    assert result.stdout.count("operator") == 4
    assert "cyclomatic" in result.stdout
    assert "maintainability" in result.stdout
    assert "raw" in result.stdout
    assert "halstead" in result.stdout
