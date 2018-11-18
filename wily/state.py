import wily.cache as cache
from wily import logger


class Index(object):
    """
    The index of the wily cache
    """
    def __init__(self, config, archiver):
        self.data = cache.get_index(self.config, archiver.name) if cache.has_index(config, archiver.name) else []

    @property
    def revisions(self):
        """
        List of all the revision indexes
        """
        return [d['revision'] for d in self.data]

class State(object):
    def __init__(self, config, archiver):
        self.config = config
        self.archiver = archiver
        self._index = None

    def ensure_exists(self):
        if not cache.exists(self.config):
            logger.debug("Wily cache not found, creating.")
            cache.create(self.config)
            logger.debug("Created wily cache")

    @property
    def index(self):
        """
        The index of the cache state
        :rtype: :class:`Index`
        """
        if self._index:
            return self._index
        else:
            self._index = Index(self.config, self.archiver)
            return self._index
