"""
Configuration of wily.

TODO : Handle operator settings. Maybe a section for each operator and then pass kwargs to operators?
TODO : Better utilise default values and factory in @dataclass to replace DEFAULT_CONFIG
 and replace the logic in load() to set default values.
"""

import configparser
import logging
import pathlib
from dataclasses import dataclass, field
from typing import Any, List

import wily.operators as operators
from wily.archivers import ARCHIVER_GIT

logger = logging.getLogger(__name__)

""" The default path name to the cache """
DEFAULT_CACHE_PATH = ".wily"


@dataclass
class WilyConfig(object):
    """
    Wily configuration.

    A data class to reflect the configurable options within Wily.
    """

    operators: List
    archiver: Any
    path: str
    max_revisions: int
    skip_ignore_check: bool = False
    cache_path: str = DEFAULT_CACHE_PATH
    targets: List[str] = None
    checkout_options: dict = field(default_factory=dict)

    def __post_init__(self):
        """Clone targets as a list of path."""
        if self.targets is None or "":
            self.targets = [self.path]


# Default values for Wily

""" The default operators """
DEFAULT_OPERATORS = {
    operators.OPERATOR_RAW.name,
    operators.OPERATOR_MAINTAINABILITY.name,
    operators.OPERATOR_CYCLOMATIC.name,
}

""" The name of the default archiver """
DEFAULT_ARCHIVER = ARCHIVER_GIT.name

""" The default configuration file name """
DEFAULT_CONFIG_PATH = "wily.cfg"

""" The default section name in the config """
DEFAULT_CONFIG_SECTION = "wily"

""" The default maximum number of revisions to archiver """
DEFAULT_MAX_REVISIONS = 50

DEFAULT_PATH = "."

""" The default configuration for Wily (if no config file exists) """
DEFAULT_CONFIG = WilyConfig(
    operators=DEFAULT_OPERATORS,
    archiver=DEFAULT_ARCHIVER,
    path=DEFAULT_PATH,
    max_revisions=DEFAULT_MAX_REVISIONS,
)

""" Default table style in console. See tabulate docs for more. """
DEFAULT_GRID_STYLE = "fancy_grid"


def load(config_path=DEFAULT_CONFIG_PATH):
    """
    Load config file and set values to defaults where no present.

    :return: The configuration ``WilyConfig``
    :rtype: :class:`wily.config.WilyConfig`
    """
    if not pathlib.Path(config_path).exists():
        logger.debug(f"Could not locate {config_path}, using default config.")
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
    max_revisions = int(
        config.get(
            section=DEFAULT_CONFIG_SECTION,
            option="max_revisions",
            fallback=DEFAULT_MAX_REVISIONS,
        )
    )

    return WilyConfig(
        operators=operators, archiver=archiver, path=path, max_revisions=max_revisions
    )
