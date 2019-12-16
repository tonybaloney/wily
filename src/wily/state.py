"""
For managing the state of the wily process.

Contains a lazy revision, index and process state model.
"""
import pathlib
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import List, Dict, Union, Optional

import wily.cache as cache
from wily import logger
from wily.archivers import Revision, Archiver, BaseArchiver
from wily.config import WilyConfig
from wily.operators import get_metric, Operator


@dataclass
class IndexedRevision(object):
    """Union of revision and the operators executed."""

    revision: Revision
    operators: List
    _data: Optional[Dict] = None

    @staticmethod
    def fromdict(d: Dict):
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

    def asdict(self) -> Dict:
        """Convert to dictionary."""
        d = asdict(self.revision)
        d["operators"] = self.operators
        return d

    def get(
        self,
        config: WilyConfig,
        archiver: Archiver,
        operator: str,
        path: Union[pathlib.Path, str],
        key: str,
    ) -> object:
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

    def get_paths(
        self, config: WilyConfig, archiver: Archiver, operator: str
    ) -> List[str]:
        """
        Get the indexed paths for this indexed revision.

        :param config: The wily config.
        :param archiver: The archiver.
        :param operator: The operator to find
        """
        if not self._data:
            self._data = cache.get(
                config=config, archiver=archiver, revision=self.revision.key
            )["operator_data"]
        logger.debug(f"Fetching keys")
        return list(self._data[operator].keys())

    def store(self, config: WilyConfig, archiver: Archiver, stats: Dict):
        """
        Store the stats for this indexed revision.

        :param config: The wily config.
        :param archiver: The archiver.
        :param stats: The data
        """
        self._data = stats
        return cache.store(config, archiver, self.revision, stats)


class Index(object):
    """The index of the wily cache."""

    def __init__(self, config: WilyConfig, archiver: Archiver):
        """
        Instantiate a new index.

        :param config: The wily config.
        :param archiver: The archiver.
        """
        self.config = config
        self.archiver = archiver
        self.data = (
            cache.get_archiver_index(config, archiver)
            if cache.has_archiver_index(config, archiver)
            else []
        )

        self._revisions = OrderedDict(
            {d["key"]: IndexedRevision.fromdict(d) for d in self.data}
        )

    def __len__(self):
        """Use length of revisions as len."""
        return len(self._revisions)

    @property
    def last_revision(self) -> IndexedRevision:
        """
        Return the most recent revision.

        :rtype: Instance of :class:`IndexedRevision`
        """
        return next(iter(self._revisions.values()))

    @property
    def revisions(self) -> List[IndexedRevision]:
        """
        List of all the revisions.

        :rtype: ``list`` of :class:`LazyRevision`
        """
        return list(self._revisions.values())

    @property
    def revision_keys(self) -> List[str]:
        """
        List of all the revision indexes.

        :rtype: ``list`` of ``str``
        """
        return list(self._revisions.keys())

    def __contains__(self, item: Union[str, Revision, IndexedRevision]) -> bool:
        """
        Check if index contains `item`.

        :param item: The item to search for

        :return: ``True`` for contains, ``False`` for not.
        """
        if isinstance(item, Revision):
            return item.key in self._revisions
        elif isinstance(item, str):
            return item in self._revisions
        else:
            raise TypeError("Invalid type for __contains__ in Index.")

    def __getitem__(self, index: str) -> IndexedRevision:
        """Get the revision for a specific index."""
        return self._revisions[index]

    def add(self, revision: Revision, operators: List[Operator]):
        """
        Add a revision to the index.

        :param revision: The revision to add to the index
        :param operators: List of operators to add
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

    def __init__(self, config: WilyConfig, archiver: Archiver = None):
        """
        Instantiate a new process state.

        :param config: The wily configuration.
        :param archiver: The archiver (optional).
        """
        if archiver:
            self.archivers = [archiver]
        else:
            self.archivers = cache.list_archivers(config)
        logger.debug(f"Initialised state indexes for archivers {self.archivers}")
        self.config = config
        self.index: Dict[str, Index] = {}
        for archiver in self.archivers:
            self.index[archiver.name] = Index(self.config, archiver)
        self.default_archiver = self.archivers[0]

    def ensure_exists(self):
        """Ensure that cache directory exists."""
        if not cache.exists(self.config):
            logger.debug("Wily cache not found, creating.")
            cache.create(self.config)
            logger.debug("Created wily cache")
        else:
            logger.debug(f"Cache {self.config.cache_path} exists")

    def get_index(self, archiver: Union[str, Archiver]) -> Index:
        if isinstance(archiver, (Archiver, BaseArchiver)):
            return self.index[archiver.name]
        return self.index[str(archiver)]

    def get_default_index(self) -> Index:
        return self.get_index(self.default_archiver)
