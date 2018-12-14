"""
Git Archiver.

Implementation of the archiver API for the gitpython module.
"""
import logging
import pathlib

from git import Repo
import git.exc

from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)

"""Possible combinations in .gitignore."""
gitignore_options = (".wily/", ".wily", ".wily/*", ".wily/**/*")


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


class WilyIgnoreGitRepositoryError(Exception):
    """Error for .wily/ being missing from .gitignore."""

    def __init__(self):
        """Raise runtime error for .gitignore being incorrectly configured."""
        self.message = "Please add '.wily/' to .gitignore before running wily"


class GitArchiver(BaseArchiver):
    """Gitpython implementation of the base archiver."""

    name = "git"

    """Whether to ignore checking for .wily/ in .gitignore files."""
    ignore_gitignore = False

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
        self.ignore_gitignore = config.skip_ignore_check
        gitignore = pathlib.Path(config.path) / ".gitignore"
        if not gitignore.exists():
            raise WilyIgnoreGitRepositoryError()

        with open(gitignore, "r") as gitignore_f:
            lines = [line.replace("\n", "") for line in gitignore_f.readlines()]
            logger.debug(lines)
            has_ignore = False
            for gitignore_opt in gitignore_options:
                if gitignore_opt in lines:
                    has_ignore = True
                    break

            if not has_ignore and not self.ignore_gitignore:  # :-/
                raise WilyIgnoreGitRepositoryError()

        self.config = config
        self.current_branch = self.repo.active_branch
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path, max_revisions):
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
            self.current_branch, max_count=max_revisions
        ):
            rev = Revision(
                key=commit.name_rev.split(" ")[0],
                author_name=commit.author.name,
                author_email=commit.author.email,
                date=commit.committed_date,
                message=commit.message,
            )
            revisions.append(rev)
        return revisions

    def checkout(self, revision, options):
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
