from git import Repo
import logging
import pathlib

from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)

""" Possible combinations in .gitignore """
gitignore_options = (".wily/", ".wily", ".wily/*", ".wily/**/*")


class DirtyGitRepositoryError(Exception):
    def __init__(self, untracked_files):
        self.untracked_files = untracked_files
        self.message = "Dirty repository, make sure you commit/stash files first"


class WilyIgnoreGitRepositoryError(Exception):
    def __init__(self):
        self.message = "Please add '.wily/' to .gitignore before running wily"


class GitArchiver(BaseArchiver):
    """ Name of the archiver """

    name = "git"

    """ Whether to ignore checking for .wily/ in .gitignore files """
    ignore_gitignore = False

    def __init__(self, config):
        self.repo = Repo(config.path)
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
                revision_date=commit.committed_date,
                message=commit.message,
            )
            revisions.append(rev)
        return revisions

    def checkout(self, revision, options):
        rev = revision.key
        self.repo.git.checkout(rev)

    def finish(self):
        # Make sure you checkout HEAD on the original branch when finishing
        self.repo.git.checkout(self.current_branch)
