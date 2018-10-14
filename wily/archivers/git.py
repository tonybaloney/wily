from git import Repo
import logging

from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)


class DirtyGitRepositoryError(Exception):
    def __init__(self, untracked_files):
        self.untracked_files = untracked_files
        self.message = "Dirty repository, make sure you commit/stash files first"


class GitArchiver(BaseArchiver):
    name = "git"

    def __init__(self, config):
        self.repo = Repo(config.path)
        self.config = config
        self.current_branch = self.repo.active_branch
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path, max_revisions):
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        # TODO : Determine current branch - how to handle detached head?
        revisions = []
        for commit in self.repo.iter_commits(
            self.current_branch, max_count=self.config.max_revisions
        ):
            rev = Revision(
                key=commit.name_rev.split(" ")[0],
                author_name=commit.author.name,
                author_email=commit.author.email,
                revision_date=commit.committed_date,
            )
            revisions.append(rev)
        return revisions

    def checkout(self, revision, options):
        rev = revision.key
        self.repo.git.checkout(rev)

    def finish(self):
        # Make sure you checkout HEAD on the original branch when finishing
        self.repo.git.checkout(self.current_branch)
