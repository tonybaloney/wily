"""
Configuration of wily.

TODO : Handle operator settings. Maybe a section for each operator and then pass kwargs to operators?
TODO : Better utilise default values and factory in @dataclass to replace DEFAULT_CONFIG
 and replace the logic in load() to set default values.
"""
import configparser
import logging
import pathlib

from wily import operators
from wily.config.types import WilyConfig
from wily.defaults import (
    DEFAULT_ARCHIVER,
    DEFAULT_CONFIG_PATH,
    DEFAULT_CONFIG_SECTION,
    DEFAULT_MAX_REVISIONS,
    DEFAULT_PATH,
)

logger = logging.getLogger(__name__)


# Default values for Wily

""" The default operators """
DEFAULT_OPERATORS = {
    operators.OPERATOR_RAW.name,
    operators.OPERATOR_MAINTAINABILITY.name,
    operators.OPERATOR_CYCLOMATIC.name,
    operators.OPERATOR_HALSTEAD.name,
}


""" The default configuration for Wily (if no config file exists) """
DEFAULT_CONFIG = WilyConfig(
    operators=DEFAULT_OPERATORS,
    archiver=DEFAULT_ARCHIVER,
    path=DEFAULT_PATH,
    max_revisions=DEFAULT_MAX_REVISIONS,
)


def load(config_path: str = DEFAULT_CONFIG_PATH) -> WilyConfig:
    """
    Load config file and set values to defaults where no present.

    :param config_path: The path where to search for the config file.
    :return: The configuration ``WilyConfig``
    """
    if not pathlib.Path(config_path).exists():
        logger.debug("Could not locate %s, using default config.", config_path)
        return DEFAULT_CONFIG

    config = configparser.ConfigParser(default_section=DEFAULT_CONFIG_SECTION)
    config.read(config_path)

    operators = config.get(
        section=DEFAULT_CONFIG_SECTION, option="operators", fallback=DEFAULT_OPERATORS
    )
    archiver = config.get(
        section=DEFAULT_CONFIG_SECTION, option="archiver", fallback=DEFAULT_ARCHIVER
    )
    path = config.get(section=DEFAULT_CONFIG_SECTION, option="path", fallback=".")
    cache_path = config.get(
        section=DEFAULT_CONFIG_SECTION, option="cache_path", fallback=""
    )
    max_revisions = config.getint(
        section=DEFAULT_CONFIG_SECTION,
        option="max_revisions",
        fallback=DEFAULT_MAX_REVISIONS,
    )
    include_ipynb = config.getboolean(
        section=DEFAULT_CONFIG_SECTION, option="include_ipynb", fallback=True
    )
    ipynb_cells = config.getboolean(
        section=DEFAULT_CONFIG_SECTION, option="ipynb_cells", fallback=True
    )

    return WilyConfig(
        operators=operators,
        archiver=archiver,
        path=path,
        _cache_path=cache_path,
        max_revisions=max_revisions,
        include_ipynb=include_ipynb,
        ipynb_cells=ipynb_cells,
    )
