"""
A module for working with the .wily/ cache directory
"""

import pathlib
import json
from wily.config import DEFAULT_CACHE_PATH
from wily.archivers import ALL_ARCHIVERS
from wily import logger


def exists():
    """
    Check whether the .wily/ directory exists

    :return: Whether the .wily directory exists
    :rtype: ``boolean``
    """
    return (
        pathlib.Path(DEFAULT_CACHE_PATH).exists()
        and pathlib.Path(DEFAULT_CACHE_PATH).is_dir()
    )


def create():
    """
    Create a wily cache
    """
    if exists():
        logger.debug("Wily cache exists, skipping")
        return
    logger.debug("Creating wily cache")
    pathlib.Path(DEFAULT_CACHE_PATH).mkdir()


def store(archiver, revision, stats):
    root = pathlib.Path(DEFAULT_CACHE_PATH) / archiver.name
    if not root.exists():
        logger.debug("Creating wily cache")
        root.mkdir()

    logger.debug(f"Creating {revision.key} output")
    with open(root / (revision.key + ".json"), "w") as out:
        out.write(json.dumps(stats, indent=2))


def store_index(archiver, index):
    root = pathlib.Path(DEFAULT_CACHE_PATH) / archiver.name
    if not root.exists():
        logger.debug("Creating wily cache")
        root.mkdir()

    logger.debug(f"Creating index output")
    with open(root / "index.json", "w") as out:
        out.write(json.dumps(index, indent=2))


def list_archivers():
    """
    List archivers with data
    :return:
    """
    root = pathlib.Path(DEFAULT_CACHE_PATH)
    result = []
    for archiver in ALL_ARCHIVERS:
        if (root / archiver.name).exists():
            result.append(archiver.name)
    return result


def get_history(archiver):
    """
    Get a list of revisions for a given archiver
    :param archiver: The archiver
    :type  archiver: ``str``

    :return: A ``list`` of ``dict``
    """
    root = pathlib.Path(DEFAULT_CACHE_PATH) / archiver
    revisions = []
    for i in root.iterdir():
        if i.name.endswith(".json"):
            with i.open() as rev_f:
                revision_data = json.load(rev_f)
                revisions.append(revision_data)
    return revisions
