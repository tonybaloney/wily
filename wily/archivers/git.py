from git import Repo

from wily.archivers import BaseArchiver


class GitArchiver(BaseArchiver):
    def __init__(self, config):
        self.repo = Repo(config.path)
        assert not self.repo.bare, "Not a Git repository"

    def revisions(self, path, max_revisions):

        pass

    def checkout(self, revision, options):
        pass

