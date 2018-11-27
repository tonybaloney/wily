"""
Archivers module.

Specifies a standard interface for finding revisions (versions) of a path and switching to them.
"""

from collections import namedtuple
from dataclasses import dataclass


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
        raise NotImplementedError


@dataclass
class Revision:
    """Represents a revision in the archiver."""

    key: str
    author_name: str
    author_email: str
    date: str
    message: str


from wily.archivers.git import GitArchiver


"""Type for an operator"""
Archiver = namedtuple("Archiver", "name cls description")


"""Git Operator defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(name="git", cls=GitArchiver, description="Git archiver")


"""Set of all available archivers"""
ALL_ARCHIVERS = {ARCHIVER_GIT}


def resolve_archiver(name):
    """
    Get the :class:`wily.archivers.Archiver` for a given name.

    :param name: The name of the archiver
    :type  name: ``str``
    :return: The archiver type
    """
    r = [archiver for archiver in ALL_ARCHIVERS if archiver.name == name.lower()]
    if not r:
        raise ValueError(f"Resolver {name} not recognised.")
    else:
        return r[0]
