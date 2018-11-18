import wily.cache as cache
from wily import logger


class Index(object):
    """
    The index of the wily cache
    """
    def __init__(self, config, archiver):
        self.config = config
        self.archiver = archiver
        self.data = cache.get_index(config, archiver.name) if cache.has_index(config, archiver.name) else []

    @property
    def revisions(self):
        """
        List of all the revision indexes
        """
        return [d['revision'] for d in self.data]
    
    def add(self, revision, operators):
        stats_header = {
                "revision": revision.key,
                "author_name": revision.author_name,
                "author_email": revision.author_email,
                "date": revision.revision_date,
                "message": revision.message,
                "operators": operators,
            }
        self.data.append(stats_header)

    def save(self):
        """
        Save the index data back to the wily cache
        """
        cache.store_index(self.config, self.archiver, self.data)

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
