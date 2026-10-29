"""
Filesystem Archiver.

Implementation of the archiver API for a standard directory (no revisions)
"""

import hashlib
import logging
import os.path
import stat
from collections.abc import Collection
from typing import Any

from wily.archivers import BaseArchiver, RevisionInfo
from wily.backend import iter_filenames
from wily.config.types import WilyConfig

logger = logging.getLogger(__name__)

# Source files larger than this are skipped rather than read into memory.
MAX_FILE_SIZE = 10 * 1024 * 1024
# Upper bound on the number of files indexed from one directory tree.
MAX_FILES = 100_000


def _is_indexable(filename: str) -> bool:
    """
    Check that a discovered file is safe to hand to the analyzer.

    Skips anything that is not a regular, readable file within the size limit,
    such as a FIFO or device named ``*.py``, which would otherwise block or
    read without limit.

    :param filename: The path to check.
    :return: True if the file should be analyzed.
    """
    try:
        file_stat = os.stat(filename)
    except OSError as e:
        logger.warning("Skipping %s: %s", filename, e)
        return False
    if not stat.S_ISREG(file_stat.st_mode):
        logger.warning("Skipping %s: not a regular file", filename)
        return False
    if file_stat.st_size > MAX_FILE_SIZE:
        logger.warning("Skipping %s: larger than %d bytes", filename, MAX_FILE_SIZE)
        return False
    if not os.access(filename, os.R_OK):
        logger.warning("Skipping %s: not readable", filename)
        return False
    return True


def _is_within(filename: str, root: str) -> bool:
    """
    Check whether a path resolves to a location inside root.

    :param filename: The path to check.
    :param root: The resolved root directory.
    :return: True if the path is root or one of its descendants.
    """
    try:
        return os.path.commonpath([root, os.path.realpath(filename)]) == root
    except ValueError:  # Different drives on Windows
        return False


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
        root = os.path.realpath(path)
        # Targets outside the root (such as the default "." when --path points
        # elsewhere) fall back to indexing the whole root.
        targets = [target for target in self.config.targets or [] if _is_within(target, root)] or [root]
        files: dict[str, None] = {}  # Ordered set: overlapping targets yield duplicates
        for filename in iter_filenames(targets, include_ipynb=self.config.include_ipynb):
            if not _is_within(filename, root):
                logger.warning("Skipping %s: outside of %s", filename, root)
                continue
            if _is_indexable(filename):
                files[os.path.relpath(os.path.realpath(filename), root).replace("\\", "/")] = None
                if len(files) > MAX_FILES:
                    raise ValueError(f"More than {MAX_FILES} files found under {root}, pass narrower targets to build")
        return [
            RevisionInfo(
                key=key,
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=int(mtime),
                message="None",
                added_files=list(files),
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
