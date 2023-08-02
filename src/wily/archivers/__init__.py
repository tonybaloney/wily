"""
Archivers module.

Specifies a standard interface for finding revisions (versions) of a path and switching to them.
"""

from dataclasses import dataclass
from typing import List, NamedTuple

from wily.config import WilyConfig


@dataclass
class Revision:
    """Represents a revision in the archiver."""

    key: str
    author_name: str
    author_email: str
    date: str
    message: str
    tracked_files: List[str]
    tracked_dirs: List[str]
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]


class BaseArchiver:
    """Abstract Archiver Class."""

    def __init__(self, config: WilyConfig, *args, **kwargs):
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
        raise NotImplementedError

    def checkout(self, revision: Revision, **options):
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :type  revision: :class:`Revision`

        :param options: Any additional options.
        :type  options: ``dict``
        """
        raise NotImplementedError

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
        raise NotImplementedError


from wily.archivers.filesystem import FilesystemArchiver
from wily.archivers.git import GitArchiver

"""Type for an operator"""


class Archiver(NamedTuple):
    name: str
    cls: BaseArchiver
    description: str

    def __str__(self):
        return self.name


"""Git Operator defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(name="git", cls=GitArchiver, description="Git archiver")

"""Filesystem archiver"""
ARCHIVER_FILESYSTEM = Archiver(
    name="filesystem", cls=FilesystemArchiver, description="Filesystem archiver"
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
