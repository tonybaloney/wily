import wily.cache as cache
from wily import logger
from wily.archivers import Revision, resolve_archiver
from wily.operators import get_metric


class LazyRevision(object):
    """
    Represents a revision within an archiver, is instantiated with index data,
    if an attribute is requested that requires loading the stored data, the cache
    will be loaded to the object.
    """

    def __init__(self, config, archiver, revision, index_dict):
        self._index_dict = index_dict
        self._cache = None
        self.config = config
        self.revision = revision
        self.archiver = archiver

    def __getattr__(self, attr):
        if attr in self._index_dict:
            return self._index_dict[attr]
        else:
            if self._cache:
                return self._cache[attr]
            else:
                self._cache = cache.get(self.config, self.archiver.name, self.revision)
                return self._cache[attr]

    def get(self, operator, path, key):
        return get_metric(self.operator_data, operator, path, key)


class Index(object):
    """
    The index of the wily cache
    """

    def __init__(self, config, archiver):
        self.config = config
        self.archiver = archiver
        self.data = (
            cache.get_index(config, archiver.name)
            if cache.has_index(config, archiver.name)
            else []
        )

    @property
    def revisions(self):
        """
        List of all the revisions
        """
        return [
            LazyRevision(self.config, self.archiver, d["revision"], d)
            for d in self.data
        ]

    @property
    def revision_keys(self):
        """
        List of all the revision indexes
        """
        return [d["revision"] for d in self.data]

    def __contains__(self, item):
        if isinstance(item, Revision):
            return item.key in self.revisions
        else:
            return item in self.revisions

    def __getitem__(self, index):
        return self.data[index]

    def add(self, revision, operators):
        """
        Add a revision to the index
        """
        stats_header = {
            "revision": revision.key,
            "author_name": revision.author_name,
            "author_email": revision.author_email,
            "date": revision.revision_date,
            "message": revision.message,
            "operators": [operator.name for operator in operators],
        }
        self.data.append(stats_header)

    def save(self):
        """
        Save the index data back to the wily cache
        """
        cache.store_index(self.config, self.archiver, self.data)


class State(object):
    def __init__(self, config, archiver=None):
        if archiver:
            self.archivers = [archiver.name]
        else:
            self.archivers = cache.list_archivers(config)
        self.config = config
        self.index = {}
        for archiver in self.archivers:
            self.index[archiver] = Index(self.config, resolve_archiver(archiver))
        self.default_archiver = self.archivers[0]

    def ensure_exists(self):
        if not cache.exists(self.config):
            logger.debug("Wily cache not found, creating.")
            cache.create(self.config)
            logger.debug("Created wily cache")
