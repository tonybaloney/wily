"""
Filesystem Archiver.

Implementation of the archiver API for a standard directory (no revisions)
"""

import hashlib
import logging
import os.path
from typing import Any, Collection

from wily.archivers import BaseArchiver, RevisionInfo
from wily.config.types import WilyConfig

logger = logging.getLogger(__name__)


class FilesystemArchiver(BaseArchiver):
    """Basic implementation of the base archiver."""

    name = "filesystem"

    def __init__(self, config: "WilyConfig"):
        """
        Instantiate a new Filesystem Archiver.

        :param config: The wily configuration
        """
        self.config = config

    def revisions(self, path: str, max_revisions: int) -> Collection[RevisionInfo]:
        """
        Get the list of revisions.

        :param path: the path to target.
        :param max_revisions: the maximum number of revisions.
        :return: A list of revisions.
        """
        mtime = os.path.getmtime(path)
        key = hashlib.sha1(str(mtime).encode()).hexdigest()[:7]  # noqa: S324
        return [
            RevisionInfo(
                key=key,
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=int(mtime),
                message="None",
                added_files=[],
                modified_files=[],
                deleted_files=[],
            )
        ]

    def checkout(self, revision: RevisionInfo, options: dict[Any, Any]) -> None:
        """
        Checkout a specific revision.

        :param revision: The revision identifier.
        :param options: Any additional options.
        """
        # effectively noop since there are no revision
        pass
