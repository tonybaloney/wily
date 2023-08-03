"""
Archivers module.

Specifies a standard interface for finding revisions (versions) of a path and switching to them.
"""

from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from wily.config.types import WilyConfig


@dataclass
class Revision:
    """Represents a revision in the archiver."""

    key: str
    author_name: Optional[str]
    author_email: Optional[str]
    date: int
    message: str
    tracked_files: List[str]
    tracked_dirs: List[str]
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]


class BaseArchiver:
    """Abstract Archiver Class."""

    name: str

    def __init__(self, config: "WilyConfig"):
        """Initialise the archiver."""
        ...

    def revisions(self, path: str, max_revisions: int) -> List[Revision]:
        """
        Get the list of revisions.

        :param path: the path to target.
        :type  path: ``str``

        :param max_revisions: the maximum number of revisions.
        :type  max_revisions: ``int``

        :return: A list of revisions.
        :rtype: ``list`` of :class:`Revision`
        """
        ...

    def checkout(self, revision: Revision, options: Dict[Any, Any]) -> None:
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :param options: Any additional options.
        """
        ...

    def finish(self):
        """Clean up any state if processing completed/failed."""
        pass

    def find(self, search: str) -> Revision:
        """
        Search a string and return a single revision.

        :param search: The search term.
        :type  search: ``str``

        :return: An instance of revision.
        :rtype: Instance of :class:`Revision`
        """
        ...


from wily.archivers.filesystem import FilesystemArchiver
from wily.archivers.git import GitArchiver

"""Type for an operator"""

T = TypeVar("T")


class Archiver(Generic[T]):
    """Holder for archivers."""

    name: str
    archiver_cls: Type[T]
    description: str

    def __init__(self, name: str, archiver_cls: Type[T], description: str):
        """Initialise the archiver."""
        self.name = name
        self.archiver_cls = archiver_cls
        self.description = description

    def __str__(self):
        """Return the name of the archiver."""
        return self.name


"""Git Operator defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(
    name="git", archiver_cls=GitArchiver, description="Git archiver"
)

"""Filesystem archiver"""
ARCHIVER_FILESYSTEM = Archiver(
    name="filesystem",
    archiver_cls=FilesystemArchiver,
    description="Filesystem archiver",
)

"""Set of all available archivers"""
ALL_ARCHIVERS = {a.name: a for a in [ARCHIVER_GIT, ARCHIVER_FILESYSTEM]}


def resolve_archiver(name: str) -> Archiver:
    """
    Get the :class:`wily.archivers.Archiver` for a given name.

    :param name: The name of the archiver
    :type  name: ``str``
    :return: The archiver type
    """
    if name not in ALL_ARCHIVERS:
        raise ValueError(f"Resolver {name} not recognised.")
    else:
        return ALL_ARCHIVERS[name.lower()]
