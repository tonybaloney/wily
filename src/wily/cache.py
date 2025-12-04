"""
A module for working with the .wily/ cache directory.

This API is not intended to be public and should not be consumed directly.
The API in this module is for archivers and commands to work with the local cache

"""

import pathlib
import shutil

from wily import logger
from wily.archivers import ALL_ARCHIVERS
from wily.config.types import WilyConfig


def exists(config: WilyConfig) -> bool:
    """
    Check whether the .wily/ directory exists.

    :param config: The configuration

    :return: Whether the .wily directory exists
    """
    return pathlib.Path(config.cache_path).exists() and pathlib.Path(config.cache_path).is_dir()



def create(config: WilyConfig) -> str:
    """
    Create a wily cache.

    :param config: The configuration
    :return: The path to the cache
    """
    if exists(config):
        logger.debug("Wily cache exists, skipping")
        return config.cache_path
    logger.debug("Creating wily cache %s", config.cache_path)
    pathlib.Path(config.cache_path).mkdir(parents=True, exist_ok=True)
    return config.cache_path


def clean(config: WilyConfig) -> None:
    """
    Delete a wily cache.

    :param config: The configuration
    """
    if not exists(config):
        logger.debug("Wily cache does not exist, skipping")
        return
    shutil.rmtree(config.cache_path)
    logger.debug("Deleted wily cache")


def list_archivers(config: WilyConfig) -> list[str]:
    """
    List the names of archivers with data.

    :param config: The configuration

    :return: A list of archiver names
    """
    root = pathlib.Path(config.cache_path)
    result = []
    for name in ALL_ARCHIVERS.keys():
        if (root / name).exists():
            result.append(name)
    return result


def has_archiver_index(config: WilyConfig, archiver: str) -> bool:
    return (pathlib.Path(config.cache_path) / archiver / "metrics.parquet").exists()


def get_archiver_index(config: WilyConfig, archiver: str) -> list:
    # TODO: Remove this completely
    return []
