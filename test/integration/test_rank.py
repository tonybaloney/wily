from click.testing import CliRunner

import wily.__main__ as main
from git import Actor, Repo


def test_rank_no_cache(tmpdir):
    """ Test the rank feature with no cache """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "rank", "src/test.py"])
    assert result.exit_code == 1, result.stdout


def test_rank_single_file_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a single file """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/test.py"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric(builddir):
    """ Test the rank feature with default (AimLow) metric on a directory """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "src/"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric_no_path(builddir):
    """ Test the rank feature with no path """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_metric_master(builddir):
    """ Test the rank feature with a specific revision. """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "-r", "master"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_default_invalid_revision(builddir):
    """ Test the rank feature with an invalid revision. """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "-r", "xyz"])
    assert result.exit_code == 1, result.stdout


def test_rank_directory_default_unindexed_revision(builddir):
    """ Test the rank feature with an unindexed revision. """
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
    """ Test the rank feature with Informational metric """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/test.py", "raw.loc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_custom_metric(builddir):
    """ Test the rank feature with AimHigh metric """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_no_path_target(builddir):
    """ Test the rank feature with no path target """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["rank", "src/", "raw.comments"])
    assert result.exit_code == 0, result.stdout


def test_rank_directory_limit(builddir):
    """ Test the rank feature with limit """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "-l 2"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_desc(builddir):
    """ Test the rank feature descending order """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--desc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_invalid_key(builddir):
    """ Test the rank feature descending order with an invalid key """
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "invalid/", "raw.comments", "--desc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_directory_asc(builddir):
    """ Test the rank feature ascending order"""
    runner = CliRunner()
    result = runner.invoke(
        main.cli, ["--path", builddir, "rank", "src/", "raw.comments", "--asc"]
    )
    assert result.exit_code == 0, result.stdout


def test_rank_total_above_threshold(builddir):
    """ Test the rank feature with total above threshold """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "--threshold=20"])
    assert result.exit_code == 0, result.stdout


def test_rank_total_below_threshold(builddir):
    """ Test the rank feature with total below threshold """
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", builddir, "rank", "--threshold=100"])
    assert result.exit_code == 1, result.stdout
