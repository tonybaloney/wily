"""
Archivers module.

Specifies a standard interface for finding revisions (versions) of a path and switching to them.
"""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from wily.config.types import WilyConfig


@dataclass
class Revision:
    """Represents a revision in the archiver."""

    key: str
    author_name: str | None
    author_email: str | None
    date: int
    message: str
    tracked_files: list[str]
    tracked_dirs: list[str]
    added_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]


class BaseArchiver:
    """Abstract Archiver Class."""

    name: str

    def __init__(self, config: "WilyConfig"):
        """Initialise the archiver."""
        ...

    def revisions(self, path: str, max_revisions: int) -> list[Revision]:
        """
        Get the list of revisions.

        :param path: the path to target.
        :param max_revisions: the maximum number of revisions.

        :return: A list of revisions.
        """
        ...

    def checkout(self, revision: Revision, options: dict[Any, Any]) -> None:
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
        :return: An instance of revision.
        """
        ...


from wily.archivers.filesystem import FilesystemArchiver  # noqa: E402
from wily.archivers.git import GitArchiver  # noqa: E402

"""Type for an Archiver"""

T = TypeVar("T")


class Archiver(Generic[T]):
    """Holder for archivers."""

    name: str
    archiver_cls: type[T]
    description: str

    def __init__(self, name: str, archiver_cls: type[T], description: str):
        """Initialise the archiver."""
        self.name = name
        self.archiver_cls = archiver_cls
        self.description = description

    def __str__(self):
        """Return the name of the archiver."""
        return self.name


"""Git Archiver defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(name="git", archiver_cls=GitArchiver, description="Git archiver")

"""Filesystem archiver"""
ARCHIVER_FILESYSTEM = Archiver(
    name="filesystem",
    archiver_cls=FilesystemArchiver,
    description="Filesystem archiver",
)

_ARCHIVERS: list[Archiver] = [ARCHIVER_GIT, ARCHIVER_FILESYSTEM]
"""Set of all available archivers"""
ALL_ARCHIVERS = {a.name: a for a in _ARCHIVERS}


def resolve_archiver(name: str) -> Archiver:
    """
    Get the :class:`wily.archivers.Archiver` for a given name.

    :param name: The name of the archiver
    :return: The archiver type
    """
    if name not in ALL_ARCHIVERS:
        raise ValueError(f"Resolver {name} not recognised.")
    else:
        return ALL_ARCHIVERS[name.lower()]
