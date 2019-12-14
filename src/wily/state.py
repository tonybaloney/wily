"""
For managing the state of the wily process.

Contains a lazy revision, index and process state model.
"""
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import List

import wily.cache as cache
from wily import logger
from wily.archivers import Revision, resolve_archiver
from wily.operators import get_metric


@dataclass
class IndexedRevision(object):
    """Union of revision and the operators executed."""

    revision: Revision
    operators: List
    _data = None

    @staticmethod
    def fromdict(d):
        """Instantiate from a dictionary."""
        rev = Revision(
            key=d["key"],
            author_name=d["author_name"],
            author_email=d["author_email"],
            date=d["date"],
            message=d["message"],
            files=d["files"] if "files" in d else [],
        )
        operators = d["operators"]
        return IndexedRevision(revision=rev, operators=operators)

    def asdict(self):
        """Convert to dictionary."""
        d = asdict(self.revision)
        d["operators"] = self.operators
        return d

    def get(self, config, archiver, operator, path, key):
        """
        Get the metric data for this indexed revision.

        :param config: The wily config.
        :type  config: :class:`wily.config.WilyConfig`

        :param archiver: The archiver.
        :type  archiver: :class:`wily.archivers.Archiver`

        :param operator: The operator to find
        :type  operator: ``str``

        :param path: The path to find
        :type  path: ``str``

        :param key: The metric key
        :type  key: ``str``
        """
        if not self._data:
            self._data = cache.get(
                config=config, archiver=archiver, revision=self.revision.key
            )["operator_data"]
        logger.debug(f"Fetching metric {path} - {key} for operator {operator}")
        return get_metric(self._data, operator, path, key)

    def get_paths(self, config, archiver, operator):
        """
        Get the indexed paths for this indexed revision.

        :param config: The wily config.
        :type  config: :class:`wily.config.WilyConfig`

        :param archiver: The archiver.
        :type  archiver: :class:`wily.archivers.Archiver`

        :param operator: The operator to find
        :type  operator: ``str``
        """
        if not self._data:
            self._data = cache.get(
                config=config, archiver=archiver, revision=self.revision.key
            )["operator_data"]
        logger.debug(f"Fetching keys")
        return list(self._data[operator].keys())

    def store(self, config, archiver, stats):
        """
        Store the stats for this indexed revision.

        :param config: The wily config.
        :type  config: :class:`wily.config.WilyConfig`

        :param archiver: The archiver.
        :type  archiver: :class:`wily.archivers.Archiver`

        :param stats: The data
        :type  stats: ``dict``
        """
        self._data = stats
        return cache.store(config, archiver, self.revision, stats)


class Index(object):
    """The index of the wily cache."""

    operators = None

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
            cache.get_archiver_index(config, archiver.name)
            if cache.has_archiver_index(config, archiver.name)
            else []
        )

        self._revisions = OrderedDict(
            {d["key"]: IndexedRevision.fromdict(d) for d in self.data}
        )

    def __len__(self):
        """Use length of revisions as len."""
        return len(self._revisions)

    @property
    def last_revision(self):
        """
        Return the most recent revision.

        :rtype: Instance of :class:`IndexedRevision`
        """
        return next(iter(self._revisions.values()))

    @property
    def revisions(self):
        """
        List of all the revisions.

        :rtype: ``list`` of :class:`LazyRevision`
        """
        return list(self._revisions.values())

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
        if isinstance(item, Revision):
            return item.key in self._revisions
        elif isinstance(item, str):
            return item in self._revisions
        else:
            raise TypeError("Invalid type for __contains__ in Index.")

    def __getitem__(self, index):
        """Get the revision for a specific index."""
        return self._revisions[index]

    def add(self, revision, operators):
        """
        Add a revision to the index.

        :param revision: The revision.
        :type  revision: :class:`Revision` or :class:`LazyRevision`
        """
        ir = IndexedRevision(
            revision=revision, operators=[operator.name for operator in operators]
        )
        self._revisions[revision.key] = ir
        return ir

    def save(self):
        """Save the index data back to the wily cache."""
        data = [i.asdict() for i in self._revisions.values()]
        logger.debug("Saving data")
        cache.store_archiver_index(self.config, self.archiver, data)


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
        logger.debug(f"Initialised state indexes for archivers {self.archivers}")
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
        else:
            logger.debug(f"Cache {self.config.cache_path} exists")
