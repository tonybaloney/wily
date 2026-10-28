import pathlib

import pytest
from click.testing import CliRunner
from git.repo.base import Repo
from git.util import Actor

import wily.__main__ as main


@pytest.fixture
def multifile_builddir(tmpdir):
    """
    A wily cache for a repo where one file is only present in the seed revision.

    ``src/stable.py`` is added in the first (seed) commit and never touched
    again, while ``src/churn.py`` is modified in a later commit. This exercises
    the delta-based storage: the latest revision only contains ``churn.py``.
    """
    repo = Repo.init(path=tmpdir)
    tmppath = pathlib.Path(tmpdir)
    (tmppath / "src").mkdir()
    stable = tmppath / "src" / "stable.py"
    churn = tmppath / "src" / "churn.py"

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    stable.write_text("def stable():\n    return 1\n")
    churn.write_text("def churn():\n    return 1\n")
    repo.index.add([str(stable), str(churn)])
    repo.index.commit(
        "seed",
        author=author,
        committer=committer,
        author_date="Thu, 07 Apr 2019 22:13:13 +0200",
        commit_date="Thu, 07 Apr 2019 22:13:13 +0200",
    )

    # Only modify churn.py in the second (latest) revision.
    churn.write_text("def churn():\n    a = 1\n    if a:\n        return a\n    return 0\n")
    repo.index.add([str(churn)])
    repo.index.commit(
        "change churn",
        author=author,
        committer=committer,
        author_date="Mon, 10 Apr 2019 22:13:13 +0200",
        commit_date="Mon, 10 Apr 2019 22:13:13 +0200",
    )

    runner = CliRunner()
    result = runner.invoke(main.cli, ["--debug", "--path", tmpdir, "build", str(tmppath / "src")])
    assert result.exit_code == 0, result.stdout

    yield tmpdir

    runner.invoke(main.cli, ["--path", tmpdir, "clean", "-y"])
    repo.close()


def test_rank_latest_includes_unchanged_files(multifile_builddir):
    """Rank at the latest revision must include files unchanged since the seed (#262)."""
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", multifile_builddir, "rank", "src/", "raw.loc", "--no-wrap"]
    )
    assert result.exit_code == 0, result.stdout
    # churn.py changed in the last commit; stable.py only exists in the seed.
    # Both must appear when ranking the latest revision.
    assert "churn.py" in result.stdout, result.stdout
    assert "stable.py" in result.stdout, result.stdout


def test_rank_no_cache(tmpdir):
    """Test the rank feature with no cache"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "rank", "src/test.py"])
    assert result.exit_code == 1, result.stdout


def test_rank_single_file_default_metric(builddir):
    """Test the rank feature with default (AimLow) metric on a single file"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/test.py"])
    assert result.exit_code == 0, result.stdout


def test_rank_single_file_default_metric_wrapped(builddir):
    """Test the rank feature with default metric and wrapping"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "--wrap", "src/test.py"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric(builddir):
    """Test the rank feature with default (AimLow) metric on a directory"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric_no_path(builddir):
    """Test the rank feature with no path"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric_master(builddir):
    """Test the rank feature with a specific revision."""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "-r", "master"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_invalid_revision(builddir):
    """Test the rank feature with an invalid revision."""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "-r", "xyz"])
    assert result.exit_code == 1, result.stdout


def test_rank_directory_default_unindexed_revision(builddir):
    """Test the rank feature with an unindexed revision."""
    repo = Repo(builddir)
    with open(builddir / "test.py", "w") as test_txt:
        test_txt.write("import abc")

    index = repo.index
    index.add([str(builddir / "test.py")])

    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit = index.commit(
        "unindexed commit",
        author=author,
        committer=committer,
        author_date="Thu, 28 Apr 2019 22:13:13 +0200",
        commit_date="Thu, 28 Apr 2019 22:13:13 +0200",
    )
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "-r", commit.hexsha])
    assert result.exit_code == 1, result.stdout


def test_rank_single_file_informational(builddir):
    """Test the rank feature with Informational metric"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/test.py", "raw.loc"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_custom_metric(builddir):
    """Test the rank feature with AimHigh metric"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/", "raw.comments"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_no_path_target(builddir):
    """Test the rank feature with no path target"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["rank", "src/", "raw.comments"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_limit(builddir):
    """Test the rank feature with limit"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "-l 2"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_desc(builddir):
    """Test the rank feature descending order"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--desc"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_invalid_key(builddir):
    """Test the rank feature descending order with an invalid key"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "invalid/", "raw.comments", "--desc"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_asc(builddir):
    """Test the rank feature ascending order"""
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--asc"])
    assert result.exit_code == 0, result.stdout
