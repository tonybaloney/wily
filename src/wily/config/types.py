"""Define a standard data class for Wily Configuration."""


import logging
import pathlib
from dataclasses import InitVar, dataclass, field
from typing import Any, Iterable, List, Optional

from wily.helper import generate_cache_path

logger = logging.getLogger(__name__)


@dataclass
class WilyConfig:
    """
    Wily configuration.

    A data class to reflect the configurable options within Wily.
    """

    operators: Iterable[str]
    archiver: Any
    path: str
    max_revisions: int
    include_ipynb: bool = True
    ipynb_cells: bool = True
    targets: Optional[List[str]] = None
    checkout_options: dict = field(default_factory=dict)
    _cache_path: InitVar[str] = ""

    def __post_init__(self, _cache_path):
        """Parse operators string to list and clone targets as a list of path."""
        if isinstance(self.operators, str):
            self.operators = self._parse_to_list(self.operators)
        if self.targets is None or "":
            self.targets = [self.path]
        self._cache_path = _cache_path  # type: ignore

    @property
    def cache_path(self):
        """Path to the cache."""
        if not self._cache_path:  # type: ignore
            self._cache_path = generate_cache_path(pathlib.Path(self.path).absolute())  # type: ignore
        return self._cache_path  # type: ignore

    @cache_path.setter
    def cache_path(self, value):
        """Override the cache path."""
        logger.debug("Setting custom cache path to %s", value)
        self._cache_path = value  # type: ignore

    @staticmethod
    def _parse_to_list(string, separator=","):
        items = []
        for raw_item in string.split(separator):
            item = raw_item.strip()
            if item:
                items.append(item)
        return items
