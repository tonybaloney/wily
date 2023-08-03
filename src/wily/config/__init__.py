"""
Configuration of wily.

TODO : Handle operator settings. Maybe a section for each operator and then pass kwargs to operators?
TODO : Better utilise default values and factory in @dataclass to replace DEFAULT_CONFIG
 and replace the logic in load() to set default values.
"""
import configparser
import hashlib
import logging
import pathlib
from functools import lru_cache

from wily import operators
from wily.archivers import ARCHIVER_GIT
from wily.config.types import WilyConfig

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def generate_cache_path(path):
    """
    Generate a reusable path to cache results.

    Will use the --path of the target and hash into
    a 9-character directory within the HOME folder.

    :return: The cache path
    :rtype: ``str``
    """
    logger.debug(f"Generating cache for {path}")
    sha = hashlib.sha1(str(path).encode()).hexdigest()[:9]
    HOME = pathlib.Path.home()
    cache_path = str(HOME / ".wily" / sha)
    logger.debug(f"Cache path is {cache_path}")
    return cache_path


# Default values for Wily

""" The default operators """
DEFAULT_OPERATORS = {
    operators.OPERATOR_RAW.name,
    operators.OPERATOR_MAINTAINABILITY.name,
    operators.OPERATOR_CYCLOMATIC.name,
    operators.OPERATOR_HALSTEAD.name,
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
