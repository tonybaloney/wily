"""
Filesystem Archiver.

Implementation of the archiver API for a standard directory (no revisions)
"""
import logging
import os.path
import hashlib
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
        mtime = os.path.getmtime(path)
        key = hashlib.sha1(str(mtime).encode()).hexdigest()[:7]
        return [
            Revision(
                key=key,
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=int(mtime),
                message="None",
                files=[],
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
