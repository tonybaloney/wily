"""
Git Archiver.

Implementation of the archiver API for the git repository using Rust backend.
"""

import logging
from collections.abc import Collection
from typing import Any

import git.exc
from git.repo import Repo

from wily.archivers import BaseArchiver, RevisionInfo
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

    def revisions(self, path: str, max_revisions: int) -> Collection[RevisionInfo]:
        """
        Get the list of revisions using Rust backend.

        :param path: the path to target.
        :param max_revisions: the maximum number of revisions.

        :return: A list of revisions.
        """
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        return get_revisions(self.repo_path, max_revisions)


    def checkout(self, revision: RevisionInfo, options: dict[Any, Any]) -> None:
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :param options: Any additional options.
        """
        checkout_revision(self.repo_path, revision["key"])

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

    def find(self, search: str) -> RevisionInfo:
        """
        Search a string and return a single revision.

        :param search: The search term (SHA prefix or full SHA).

        :return: An instance of revision.
        """
        # Use Rust backend to find the revision by SHA prefix
        rev_data = find_revision(self.repo_path, search)
        if rev_data is None:
            raise ValueError(f"Revision not found: {search}")
        return rev_data
