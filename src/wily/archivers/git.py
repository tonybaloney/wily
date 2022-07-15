"""
Git Archiver.

Implementation of the archiver API for the gitpython module.
"""
import logging
from typing import Dict, Tuple, List

from git import Commit
from git.repo import Repo
import git.exc

from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)


class InvalidGitRepositoryError(Exception):
    """Error for when a folder is not a git repo."""

    pass


class DirtyGitRepositoryError(Exception):
    """Error for a dirty git repository (untracked files)."""

    def __init__(self, untracked_files):
        """
        Raise error for untracked files.

        :param untracked_files: List of untracked files
        :param untracked_files: ``list``
        """
        self.untracked_files = untracked_files
        self.message = "Dirty repository, make sure you commit/stash files first"


def get_tracked_files_dirs(repo: Repo, commit: Commit) -> Tuple[List[str], List[str]]:
    """Get tracked files in a repo for a commit hash using ls-tree."""
    paths = repo.git.execute(
        ["git", "ls-tree", "--name-only", "--full-tree", "-r", commit.hexsha]
    ).split("\n")
    dirs = [""] + repo.git.execute(
        ["git", "ls-tree", "--name-only", "--full-tree", "-r", "-d", commit.hexsha]
    ).split("\n")
    return paths, dirs


def whatchanged(commit_a: Commit, commit_b: Commit) -> Tuple[List[str], List[str], List[str]]:
    """Get files added, modified and deleted between commits."""
    diffs = commit_b.diff(commit_a)
    added_files = []
    modified_files = []
    deleted_files = []
    for diff in diffs:
        if diff.new_file:
            added_files.append(diff.b_path)
        elif diff.deleted_file:
            deleted_files.append(diff.a_path)
        elif diff.renamed_file:
            added_files.append(diff.b_path)
            deleted_files.append(diff.a_path)
        elif diff.change_type == "M":
            modified_files.append(diff.a_path)
    return added_files, modified_files, deleted_files


class GitArchiver(BaseArchiver):
    """Gitpython implementation of the base archiver."""

    name = "git"

    def __init__(self, config):
        """
        Instantiate a new Git Archiver.

        :param config: The wily configuration
        :type  config: :class:`wily.config.WilyConfig`
        """
        try:
            self.repo = Repo(config.path)
        except git.exc.InvalidGitRepositoryError as e:
            raise InvalidGitRepositoryError from e

        self.config = config
        if self.repo.head.is_detached:
            self.current_branch = self.repo.head.object.hexsha
        else:
            self.current_branch = self.repo.active_branch
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path: str, max_revisions: int) -> List[Revision]:
        """
        Get the list of revisions.

        :param path: the path to target.
        :type  path: ``str``

        :param max_revisions: the maximum number of revisions.
        :type  max_revisions: ``int``

        :return: A list of revisions.
        :rtype: ``list`` of :class:`Revision`
        """
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        revisions = []
        for commit in self.repo.iter_commits(
            self.current_branch, max_count=max_revisions, reverse=True
        ):
            tracked_files, tracked_dirs = get_tracked_files_dirs(self.repo, commit)
            if not commit.parents or not revisions:
                added_files = tracked_files
                modified_files = []
                deleted_files = []
            else:
                added_files, modified_files, deleted_files = whatchanged(
                    commit, self.repo.commit(commit.hexsha + "~1")
                )

            logger.debug(f"For revision {commit.name_rev.split(' ')[0]} found:")
            logger.debug(f"Tracked files: {tracked_files}")
            logger.debug(f"Tracked directories: {tracked_dirs}")
            logger.debug(f"Added files: {added_files}")
            logger.debug(f"Modified files: {modified_files}")
            logger.debug(f"Deleted files: {deleted_files}")

            rev = Revision(
                key=commit.name_rev.split(" ")[0],
                author_name=commit.author.name,
                author_email=commit.author.email,
                date=commit.committed_date,
                message=commit.message,
                tracked_files=tracked_files,
                tracked_dirs=tracked_dirs,
                added_files=added_files,
                modified_files=modified_files,
                deleted_files=deleted_files,
            )
            revisions.append(rev)
        return revisions[::-1]

    def checkout(self, revision: Revision, options: Dict):
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :type  revision: :class:`Revision`

        :param options: Any additional options.
        :type  options: ``dict``
        """
        rev = revision.key
        self.repo.git.checkout(rev)

    def finish(self):
        """
        Clean up any state if processing completed/failed.

        For git, will checkout HEAD on the original branch when finishing
        """
        self.repo.git.checkout(self.current_branch)
        self.repo.close()

    def find(self, search: str) -> Revision:
        """
        Search a string and return a single revision.

        :param search: The search term.
        :type  search: ``str``

        :return: An instance of revision.
        :rtype: Instance of :class:`Revision`
        """
        commit = self.repo.commit(search)
        tracked_files, tracked_dirs = get_tracked_files_dirs(self.repo, commit)
        if not commit.parents:
            added_files = tracked_files
            modified_files = []
            deleted_files = []
        else:
            added_files, modified_files, deleted_files = whatchanged(
                commit, self.repo.commit(commit.hexsha + "~1")
            )

        return Revision(
            key=commit.name_rev.split(" ")[0],
            author_name=commit.author.name,
            author_email=commit.author.email,
            date=commit.committed_date,
            message=commit.message,
            tracked_files=tracked_files,
            tracked_dirs=tracked_dirs,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
        )
