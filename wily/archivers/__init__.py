from collections import namedtuple


class BaseArchiver(object):
    """Abstract Archiver Class"""

    def log(self, path, max_revisions):
        """
        Get the list of revision
        :param path: the path
        :param max_revisions: the maximum number of revisions
        :return:
        """
        raise NotImplementedError()


    def checkout(self, revision, options):
        """
        Checkout a specific revision
        :param revision: The revision identifier
        :param options: Any additional options
        """
        raise NotImplementedError()


from wily.archivers.git import GitArchiver


"""Type for an operator"""
Archiver = namedtuple("Archiver", "name cls description")


"""Git Operator defined in `wily.archivers.git`"""
ARCHIVER_GIT = Archiver(name="git", cls=GitArchiver, description="Git archiver")


"""Set of all available archivers"""
ALL_ARCHIVERS = {
    ARCHIVER_GIT
}


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
