"""
Configuration of wily

TODO : Handle operator settings. Maybe a section for each operator and then pass kwargs to operators?
TODO : Better utilise default values and factory in @dataclass to replace DEFAULT_CONFIG
 and replace the logic in load() to set default values.
"""

import configparser
import pathlib
import logging
from attr import attrs, attrib

import wily.operators as operators
from wily.archivers import ARCHIVER_GIT

logger = logging.getLogger(__name__)

""" The default path name to the cache """
DEFAULT_CACHE_PATH = ".wily"


@attrs
class WilyConfig(object):
    """
    A data class to reflect the configurable options
    within Wily.
    """

    operators = attrib()
    archiver = attrib()
    path = attrib()
    max_revisions = attrib()
    skip_ignore_check = attrib(default=False)
    cache_path = attrib(default=DEFAULT_CACHE_PATH)
    targets = attrib(default=None)
    checkout_options = attrib(default={})

    def __post_init__(self):
        # Clone targets as a list of path
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
        logger.debug("Could not locate {0}, using default config.".format(config_path))
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
