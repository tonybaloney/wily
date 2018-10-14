"""
A module for working with the .wily/ cache directory
"""

import pathlib
import json
from wily.config import DEFAULT_CACHE_PATH


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
        return
    pathlib.Path(DEFAULT_CACHE_PATH).mkdir()


def store(archiver, revision, stats):
    root = pathlib.Path(DEFAULT_CACHE_PATH) / archiver.name
    if not root.exists():
        root.mkdir()

    with open(root / (revision.key + ".json"), "w") as out:
        json.dump(out, stats, indent=2)
