"""
Archivers module.

Specifies a standard interface for finding revisions (versions) of a path and switching to them.
"""

from collections import namedtuple
from dataclasses import dataclass
from typing import List


class BaseArchiver(object):
    """Abstract Archiver Class."""

    def revisions(self, path, max_revisions):
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

    def checkout(self, revision, **options):
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

    def find(self, search):
        """
        Search a string and return a single revision.

        :param search: The search term.
        :type  search: ``str``

        :return: An instance of revision.
        :rtype: Instance of :class:`Revision`
        """
        raise NotImplementedError


@dataclass
class Revision:
    """Represents a revision in the archiver."""

    key: str
    author_name: str
    author_email: str
    date: str
    message: str
    files: List[str]


from wily.archivers.git import GitArchiver
from wily.archivers.filesystem import FilesystemArchiver


"""Type for an operator"""
Archiver = namedtuple("Archiver", "name cls description")


"""Git Operator defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(name="git", cls=GitArchiver, description="Git archiver")

"""Filesystem archiver"""
ARCHIVER_FILESYSTEM = Archiver(
    name="filesystem", cls=FilesystemArchiver, description="Filesystem archiver"
)

"""Set of all available archivers"""
ALL_ARCHIVERS = {a.name: a for a in [ARCHIVER_GIT, ARCHIVER_FILESYSTEM]}


def resolve_archiver(name):
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
