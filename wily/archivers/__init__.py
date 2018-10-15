from collections import namedtuple
from dataclasses import dataclass


class BaseArchiver(object):
    """Abstract Archiver Class"""

    def revisions(self, path, max_revisions):
        """
        Get the list of revision
        :param path: the path
        :type  path: ``str``

        :param max_revisions: the maximum number of revisions
        :type  max_revisions: ``int``

        :return: A list of revisions
        :rtype: ``list`` of :class:`Revision`
        """
        raise NotImplementedError()

    def checkout(self, revision, **options):
        """
        Checkout a specific revision
        :param revision: The revision identifier
        :type  revision: :class:`Revision`

        :param options: Any additional options
        :type  options: ``dict``
        """
        raise NotImplementedError()


@dataclass
class Revision:
    key: str
    author_name: str
    author_email: str
    revision_date: str
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
    Get the :namedtuple:`wily.archivers.Archiver` for a given name
    :param name: The name of the archiver
    :return: The archiver type
    """
    r = [archiver for archiver in ALL_ARCHIVERS if archiver.name == name.lower()]
    if not r:
        raise ValueError(f"Resolver {name} not recognised.")
    else:
        return r[0]
