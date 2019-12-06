"""
A module for working with the .wily/ cache directory.

This API is not intended to be public and should not be consumed directly.
The API in this module is for archivers and commands to work with the local cache

"""

import json
import os.path
import pathlib
import shutil

from wily import logger, __version__
from wily.archivers import ALL_ARCHIVERS
from wily.operators import resolve_operator


def exists(config):
    """
    Check whether the .wily/ directory exists.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :return: Whether the .wily directory exists
    :rtype: ``boolean``
    """
    exists = (
        pathlib.Path(config.cache_path).exists()
        and pathlib.Path(config.cache_path).is_dir()
    )
    if not exists:
        return False
    index_path = pathlib.Path(config.cache_path) / "index.json"
    if index_path.exists():
        with open(index_path, "r") as out:
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


def create_index(config):
    """Create the root index."""
    filename = pathlib.Path(config.cache_path) / "index.json"
    index = {"version": __version__}
    with open(filename, "w") as out:
        out.write(json.dumps(index, indent=2))


def create(config):
    """
    Create a wily cache.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :return: The path to the cache
    :rtype: ``str``
    """
    if exists(config):
        logger.debug("Wily cache exists, skipping")
        return config.cache_path
    logger.debug(f"Creating wily cache {config.cache_path}")
    pathlib.Path(config.cache_path).mkdir(parents=True, exist_ok=True)
    create_index(config)
    return config.cache_path


def clean(config):
    """
    Delete a wily cache.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    """
    if not exists(config):
        logger.debug("Wily cache does not exist, skipping")
        return
    shutil.rmtree(config.cache_path)
    logger.debug("Deleted wily cache")


def store(config, archiver, revision, stats):
    """
    Store a revision record within an archiver folder.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param archiver: The name of the archiver type (e.g. 'git')
    :type  archiver: ``str``
    
    :param revision: The revision ID
    :type  revision: ``str``
    
    :param stats: The collected data
    :type  stats: ``dict``
    
    :return: The absolute path to the created file
    :rtype: ``str``

    :rtype: `pathlib.Path`
    """
    root = pathlib.Path(config.cache_path) / archiver.name

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

    logger.debug(f"Creating {revision.key} output")
    filename = root / (revision.key + ".json")
    if filename.exists():
        raise RuntimeError(f"File {filename} already exists, index may be corrupt.")
    with open(filename, "w") as out:
        out.write(json.dumps(stats, indent=2))
    return filename


def store_archiver_index(config, archiver, index):
    """
    Store an archiver's index record for faster search.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param archiver: The name of the archiver type (e.g. 'git')
    :type  archiver: ``str``
    
    :param index: The archiver index record
    :type  index: ``dict``

    :rtype: `pathlib.Path`
    """
    root = pathlib.Path(config.cache_path) / archiver.name

    if not root.exists():
        root.mkdir()
        logger.debug("Created archiver directory")

    index = sorted(index, key=lambda k: k["date"], reverse=True)

    filename = root / "index.json"
    with open(filename, "w") as out:
        out.write(json.dumps(index, indent=2))
    logger.debug(f"Created index output")
    return filename


def list_archivers(config):
    """
    List the names of archivers with data.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :return: A list of archiver names
    :rtype: ``list`` of ``str``
    """
    root = pathlib.Path(config.cache_path)
    result = []
    for name in ALL_ARCHIVERS.keys():
        if (root / name).exists():
            result.append(name)
    return result


def get_default_metrics(config):
    """
    Get the default metrics for a configuration.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :return: Return the list of default metrics in this index
    :rtype: ``list`` of ``str``
    """
    archivers = list_archivers(config)
    default_metrics = []

    for archiver in archivers:
        index = get_archiver_index(config, archiver)

        if len(index) == 0:
            logger.warning("No records found in the index, no metrics available")
            return []

        operators = index[0]["operators"]
        for operator in operators:
            o = resolve_operator(operator)
            if o.cls.default_metric_index is not None:
                metric = o.cls.metrics[o.cls.default_metric_index]
                default_metrics.append("{0}.{1}".format(o.cls.name, metric.name))
    return default_metrics


def has_archiver_index(config, archiver):
    """
    Check if this archiver has an index file.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param archiver: The name of the archiver type (e.g. 'git')
    :type  archiver: ``str``

    :return: the exist
    :rtype: ``bool``
    """
    root = pathlib.Path(config.cache_path) / archiver / "index.json"
    return root.exists()


def get_archiver_index(config, archiver):
    """
    Get the contents of the archiver index file.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param archiver: The name of the archiver type (e.g. 'git')
    :type  archiver: ``str``
    
    :return: The index data
    :rtype: ``dict``
    """
    root = pathlib.Path(config.cache_path) / archiver
    with (root / "index.json").open("r") as index_f:
        index = json.load(index_f)
    return index


def get(config, archiver, revision):
    """
    Get the data for a given revision.

    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param archiver: The name of the archiver type (e.g. 'git')
    :type  archiver: ``str``
    
    :param revision: The revision ID
    :type  revision: ``str``
    
    :return: The data record for that revision
    :rtype: ``dict``
    """
    root = pathlib.Path(config.cache_path) / archiver
    # TODO : string escaping!!!
    with (root / f"{revision}.json").open("r") as rev_f:
        index = json.load(rev_f)
    return index
