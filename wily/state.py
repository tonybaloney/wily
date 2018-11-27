"""
For managing the state of the wily process.

Contains a lazy revision, index and process state model.
"""
from collections import OrderedDict
import wily.cache as cache
from wily import logger
from wily.archivers import Revision, resolve_archiver
from wily.operators import get_metric


class LazyRevision(object):
    """
    Represents a revision within an archiver.

    Is instantiated with index data,
    if an attribute is requested that requires loading the stored data, the cache
    will be loaded to the object.
    """

    def __init__(self, config, archiver, revision, index_dict):
        """
        Instantiate a lazy revision.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`

        :param archiver: The archiver.
        :type  archiver: :class:`wily.archivers.Archiver`

        :param revision: The revision ID.
        :type  revision: ``str``

        :param index_dict: The index dictionary.
        :type  index_dict: ``dict``
        """
        self._index_dict = index_dict
        self._cache = None
        self.config = config
        self.revision = revision
        self.key = revision
        self.archiver = archiver

    def __getattr__(self, attr):
        """Override default __getattr__ to fetch data from cache."""
        if attr in self._index_dict:
            return self._index_dict[attr]
        else:
            if self._cache:
                return self._cache[attr]
            else:
                self._cache = cache.get(self.config, self.archiver.name, self.revision)
                return self._cache[attr]

    def get(self, operator, path, key):
        """Get the data from wily cache."""
        return get_metric(self.operator_data, operator, path, key)


class Index(object):
    """The index of the wily cache."""

    def __init__(self, config, archiver):
        """
        Instantiate a new index.

        :param config: The wily config.
        :type  config: :class:`wily.config.WilyConfig`

        :param archiver: The archiver.
        :type  archiver: :class:`wily.archivers.Archiver`
        """
        self.config = config
        self.archiver = archiver
        self.data = (
            cache.get_index(config, archiver.name)
            if cache.has_index(config, archiver.name)
            else []
        )
        # If only Python supported Ordered Dict comprehensions :-(
        self._revisions = OrderedDict()
        for d in self.data:
            self.add(LazyRevision(self.config, self.archiver, d["revision"], d))

    def __len__(self):
        """Use length of revisions as len."""
        return len(self._revisions)

    @property
    def revisions(self):
        """
        List of all the revisions.

        :rtype: ``list`` of :class:`LazyRevision`
        """
        return [LazyRevision(self.config, self.archiver, r['revision'], r) for r in self._revisions.values()]

    @property
    def revision_keys(self):
        """
        List of all the revision indexes.

        :rtype: ``list`` of ``str``
        """
        return list(self._revisions.keys())

    def __contains__(self, item):
        """
        Check if index contains `item`.

        :param item: The item to search for
        :type  item: ``str``, :class:`Revision` or :class:`LazyRevision`

        :return: ``True`` for contains, ``False`` for not.
        """
        if isinstance(item, (Revision, LazyRevision)):
            return item.key in self._revisions
        elif isinstance(item, str):
            return item in self._revisions
        else:
            raise TypeError("Invalid type for __contains__ in Index.")

    def __getitem__(self, index):
        """Get the revision for a specific index."""
        return self._revisions[index]

    def add(self, revision, operators=[]):
        """
        Add a revision to the index.

        :param revision: The revision.
        :type  revision: :class:`Revision` or :class:`LazyRevision`
        """
        stats_header = {
            "revision": revision.key,
            "author_name": revision.author_name,
            "author_email": revision.author_email,
            "date": revision.date,
            "message": revision.message,
            "operators": [operator.name for operator in operators],
        }
        self._revisions[revision.key] = stats_header

    def save(self):
        """Save the index data back to the wily cache."""
        cache.store_index(self.config, self.archiver, list(self._revisions.values()))


class State(object):
    """
    The wily process state.

    Includes indexes for each archiver.
    """

    def __init__(self, config, archiver=None):
        """
        Instantiate a new process state.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`

        :param archiver: The archiver (optional).
        :type  archiver: :class:`wily.archivers.Archiver`
        """
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
        """Ensure that cache directory exists."""
        if not cache.exists(self.config):
            logger.debug("Wily cache not found, creating.")
            cache.create(self.config)
            logger.debug("Created wily cache")
