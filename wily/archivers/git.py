from git import Repo

from wily.archivers import BaseArchiver


class DirtyGitRepositoryError(RuntimeError):
    def __init__(self, untracked_files):
        self.untracked_files= untracked_files
        self.message = "Dirty repository, make sure you commit/stash files first"


class GitArchiver(BaseArchiver):
    def __init__(self, config):
        self.repo = Repo(config.path)
        self.config = config
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path, max_revisions):
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        # TODO : Determine current branch - how to handle detached head?
        return list(self.repo.iter_commits('master', max_count=self.config.max_revisions))

    def checkout(self, revision, options):
        pass

