"""
Git Archiver.

Implementation of the archiver API for the git repository using Rust backend.
"""

import logging
from typing import Any

import git.exc
from git.repo import Repo

from wily.archivers import BaseArchiver, Revision
from wily.backend import checkout_branch, checkout_revision, find_revision, get_revisions
from wily.config.types import WilyConfig

logger = logging.getLogger(__name__)


class InvalidGitRepositoryError(Exception):
    """Error for when a folder is not a git repo."""

    pass


class DirtyGitRepositoryError(Exception):
    """Error for a dirty git repository (untracked files)."""

    def __init__(self, untracked_files: list[str]):
        """
        Raise error for untracked files.

        :param untracked_files: List of untracked files
        :param untracked_files: ``list``
        """
        self.untracked_files = untracked_files
        self.message = "Dirty repository, make sure you commit/stash files first"


class GitArchiver(BaseArchiver):
    """Git implementation of the base archiver using Rust backend."""

    name = "git"

    def __init__(self, config: "WilyConfig"):
        """
        Instantiate a new Git Archiver.

        :param config: The wily configuration
        """
        try:
            # We still use gitpython for initial validation and dirty check
            self.repo = Repo(config.path)
        except git.exc.InvalidGitRepositoryError as e:
            raise InvalidGitRepositoryError from e

        self.config = config
        self.repo_path = str(config.path)

        if self.repo.head.is_detached:
            self.current_branch = self.repo.head.object.hexsha
        else:
            self.current_branch = str(self.repo.active_branch)
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path: str, max_revisions: int) -> list[Revision]:
        """
        Get the list of revisions using Rust backend.

        :param path: the path to target.
        :param max_revisions: the maximum number of revisions.

        :return: A list of revisions.
        """
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        revisions = get_revisions(self.repo_path, max_revisions, self.current_branch)

        result: list[Revision] = []
        for rev_data in revisions:
            logger.debug("For revision %s found:", rev_data["key"])
            logger.debug("Tracked files: %s", rev_data["tracked_files"])
            logger.debug("Tracked directories: %s", rev_data["tracked_dirs"])
            logger.debug("Added files: %s", rev_data["added_files"])
            logger.debug("Modified files: %s", rev_data["modified_files"])
            logger.debug("Deleted files: %s", rev_data["deleted_files"])

            rev = Revision(
                key=rev_data["key"],
                author_name=rev_data["author_name"],
                author_email=rev_data["author_email"],
                date=rev_data["date"],
                message=rev_data["message"],
                tracked_files=rev_data["tracked_files"],
                tracked_dirs=rev_data["tracked_dirs"],
                added_files=rev_data["added_files"],
                modified_files=rev_data["modified_files"],
                deleted_files=rev_data["deleted_files"],
            )
            result.append(rev)

        return result

    def checkout(self, revision: Revision, options: dict[Any, Any]) -> None:
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :param options: Any additional options.
        """
        checkout_revision(self.repo_path, revision.key)

    def finish(self):
        """
        Clean up any state if processing completed/failed.

        For git, will checkout HEAD on the original branch when finishing
        """
        try:
            checkout_branch(self.repo_path, self.current_branch)
        except ValueError:
            # If branch checkout fails, try as a revision (for detached HEAD)
            checkout_revision(self.repo_path, self.current_branch)
        self.repo.close()

    def find(self, search: str) -> Revision:
        """
        Search a string and return a single revision.

        :param search: The search term (SHA prefix or full SHA).

        :return: An instance of revision.
        """
        # Use Rust backend to find the revision by SHA prefix
        rev_data = find_revision(self.repo_path, search)
        if rev_data is None:
            raise ValueError(f"Revision not found: {search}")

        return Revision(
            key=rev_data["key"],
            author_name=rev_data["author_name"],
            author_email=rev_data["author_email"],
            date=rev_data["date"],
            message=rev_data["message"],
            tracked_files=list(rev_data["tracked_files"]),
            tracked_dirs=list(rev_data["tracked_dirs"]),
            added_files=list(rev_data["added_files"]),
            modified_files=list(rev_data["modified_files"]),
            deleted_files=list(rev_data["deleted_files"]),
        )
