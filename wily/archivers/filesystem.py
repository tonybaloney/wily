"""
Filesystem Archiver.

Implementation of the archiver API for a standard directory (no revisions)
"""
import logging

from wily.archivers import BaseArchiver, Revision

logger = logging.getLogger(__name__)


class FilesystemArchiver(BaseArchiver):
    """Basic implementation of the base archiver."""

    name = "filesystem"

    def __init__(self, config):
        """
        Instantiate a new Filesystem Archiver.

        :param config: The wily configuration
        :type  config: :class:`wily.config.WilyConfig`
        """
        self.config = config

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
        # TODO : Sha the current file/path
        # so if the files change, the revision is redundant
        return [
            Revision(
                key="current",
                author_name="Local User",
                author_email="-",
                date="Current",
                message="None",
            )
        ]

    def checkout(self, revision, options):
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :type  revision: :class:`Revision`

        :param options: Any additional options.
        :type  options: ``dict``
        """
        # effectively noop since there are no revision
        pass
