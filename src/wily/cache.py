"""
A module for working with the .wily/ cache directory.

This API is not intended to be public and should not be consumed directly.
The API in this module is for archivers and commands to work with the local cache

"""

import json
import os.path
import pathlib
import shutil
from typing import Any, Dict, List, Union

from wily import __version__, logger
from wily.archivers import ALL_ARCHIVERS, Archiver, Revision
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import resolve_operator


def exists(config: WilyConfig) -> bool:
    """
    Check whether the .wily/ directory exists.

    :param config: The configuration

    :return: Whether the .wily directory exists
    """
    exists = (
        pathlib.Path(config.cache_path).exists()
        and pathlib.Path(config.cache_path).is_dir()
    )
    if not exists:
        return False
    index_path = pathlib.Path(config.cache_path) / "index.json"
    if index_path.exists():
        with open(index_path) as out:
            index = json.load(out)
        if index["version"] != __version__:
            # TODO: Inspect the versions properly.
            logger.warning(
                "Wily cache is old, you may incur errors until you rebuild the cache."
            )
    else:
        logger.warning(
            "Wily cache was not versioned, you may incur errors until you rebuild the cache."
        )
        create_index(config)
    return True


def create_index(config: WilyConfig) -> None:
    """Create the root index."""
    filename = pathlib.Path(config.cache_path) / "index.json"
    index = {"version": __version__}
    with open(filename, "w") as out:
        out.write(json.dumps(index, indent=2))


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
    create_index(config)
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


def store(
    config: WilyConfig,
    archiver: Union[Archiver, str],
    revision: Revision,
    stats: Dict[str, Any],
) -> pathlib.Path:
    """
    Store a revision record within an archiver folder.

    :param config: The configuration
    :param archiver: The archiver to get name from (e.g. 'git')
    :param revision: The revision
    :param stats: The collected data

    :return: The absolute path to the created file
    """
    root = pathlib.Path(config.cache_path) / str(archiver)

    if not root.exists():
        logger.debug("Creating wily cache")
        root.mkdir()

    # fix absolute path references.
    if config.path != ".":
        for operator, operator_data in list(stats["operator_data"].items()):
            if operator_data:
                new_operator_data = operator_data.copy()
                for k, v in list(operator_data.items()):
                    if os.path.isabs(k):
                        new_key = os.path.relpath(str(k), str(config.path))
                    else:
                        new_key = str(k)
                    del new_operator_data[k]
                    new_operator_data[new_key] = v
                del stats["operator_data"][operator]
                stats["operator_data"][operator] = new_operator_data

    logger.debug("Creating %s output", revision.key)
    filename = root / (revision.key + ".json")
    if filename.exists():
        raise RuntimeError(f"File {filename} already exists, index may be corrupt.")
    with open(filename, "w") as out:
        out.write(json.dumps(stats, indent=2))
    return filename


def store_archiver_index(
    config: WilyConfig, archiver: Union[Archiver, str], index: List[Dict[str, Any]]
) -> pathlib.Path:
    """
    Store an archiver's index record for faster search.

    :param config: The configuration
    :param archiver: The archiver to get name from (e.g. 'git')
    :param index: The archiver index record

    :return: The absolute path to the created file
    """
    root = pathlib.Path(config.cache_path) / str(archiver)

    if not root.exists():
        root.mkdir()
        logger.debug("Created archiver directory")

    index = sorted(index, key=lambda k: k["date"], reverse=True)

    filename = root / "index.json"
    with open(filename, "w") as out:
        out.write(json.dumps(index, indent=2))
    logger.debug("Created index output")
    return filename


def list_archivers(config: WilyConfig) -> List[str]:
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


def get_default_metrics(config: WilyConfig) -> List[str]:
    """
    Get the default metrics for a configuration.

    :param config: The configuration
    :return: Return the list of default metrics in this index
    """
    archivers = list_archivers(config)
    default_metrics = []

    for archiver in archivers:
        index = get_archiver_index(config, archiver)

        if len(index) == 0:
            logger.warning(_("No records found in the index, no metrics available"))
            return []

        operators = index[0]["operators"]
        for operator in operators:
            o = resolve_operator(operator)
            if o.operator_cls.default_metric_index is not None:
                metric = o.operator_cls.metrics[o.operator_cls.default_metric_index]
                default_metrics.append(f"{o.operator_cls.name}.{metric.name}")
    return default_metrics


def has_archiver_index(config: WilyConfig, archiver: Union[Archiver, str]) -> bool:
    """
    Check if this archiver has an index file.

    :param config: The configuration
    :param archiver: The name of the archiver type (e.g. 'git')

    :return: Whether the archiver's index exists.
    """
    root = pathlib.Path(config.cache_path) / str(archiver) / "index.json"
    return root.exists()


def get_archiver_index(config: WilyConfig, archiver: Union[Archiver, str]) -> Any:
    """
    Get the contents of the archiver index file.

    :param config: The configuration
    :param archiver: The name of the archiver type (e.g. 'git')
    :return: The index data
    """
    root = pathlib.Path(config.cache_path) / str(archiver)
    with (root / "index.json").open("r") as index_f:
        index = json.load(index_f)
    return index


def get(
    config: WilyConfig, archiver: Union[Archiver, str], revision: str
) -> Dict[Any, Any]:
    """
    Get the data for a given revision.

    :param config: The configuration
    :param archiver: The archiver to get name from (e.g. 'git')
    :param revision: The revision ID
    :return: The data record for that revision
    """
    root = pathlib.Path(config.cache_path) / str(archiver)
    # TODO : string escaping!!!
    with (root / f"{revision}.json").open("r") as rev_f:
        index = json.load(rev_f)
    return index
