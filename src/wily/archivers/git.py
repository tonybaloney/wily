"""
Git Archiver.

Implementation of the archiver API for the gitpython module.
"""
import logging
from typing import List, Dict

from git import Repo
import git.exc

from wily.config import WilyConfig
from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)


class InvalidGitRepositoryError(Exception):
    """Error for when a folder is not a git repo."""

    pass


class DirtyGitRepositoryError(Exception):
    """Error for a dirty git repository (untracked files)."""

    def __init__(self, untracked_files: List[str]):
        """
        Raise error for untracked files.

        :param untracked_files: List of untracked files
        """
        self.untracked_files: List[str] = untracked_files
        self.message: str = "Dirty repository, make sure you commit/stash files first"


class GitArchiver(BaseArchiver):
    """Gitpython implementation of the base archiver."""

    repo: Repo
    name: str = "git"

    def __init__(self, config: WilyConfig):
        """
        Instantiate a new Git Archiver.

        :param config: The wily configuration
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
        :param max_revisions: the maximum number of revisions.

        :return: A list of revisions.
        """
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        revisions: List[Revision] = []
        for commit in self.repo.iter_commits(
            self.current_branch, max_count=max_revisions
        ):
            rev = Revision(
                key=commit.name_rev.split(" ")[0],
                author_name=commit.author.name,
                author_email=commit.author.email,
                date=commit.committed_date,
                message=commit.message,
                files=list(commit.stats.files.keys()),
            )
            revisions.append(rev)
        return revisions

    def checkout(self, revision: Revision, options: Dict):
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :param options: Any additional options.
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

        :return: An instance of revision.
        """
        commit = self.repo.commit(search)

        return Revision(
            key=commit.name_rev.split(" ")[0],
            author_name=commit.author.name,
            author_email=commit.author.email,
            date=commit.committed_date,
            message=commit.message,
            files=list(commit.stats.files.keys()),
        )
