"""
Configuration of wily

"""

import configparser
from collections import namedtuple
import pathlib
import logging

from wily.operators import OPERATOR_MCCABE
from wily.archivers import ARCHIVER_GIT

logger = logging.getLogger("wily")


WilyConfig = namedtuple("WilyConfig", "operators archiver")

DEFAULT_OPERATORS = {OPERATOR_MCCABE.name}

DEFAULT_ARCHIVER = ARCHIVER_GIT.name

DEFAULT_CONFIG = WilyConfig(operators=DEFAULT_OPERATORS, archiver=DEFAULT_ARCHIVER)

DEFAULT_CONFIG_PATH = "wily.cfg"

DEFAULT_CACHE_PATH = ".wily"


def load(config_path=DEFAULT_CONFIG_PATH):
    """
    Load config file

    :return: The configuration ``WilyConfig``
    """
    if not pathlib.Path(config_path).exists():
        logger.debug(f"Could not locate {config_path}, using default config.")
        return DEFAULT_CONFIG

    config = configparser.ConfigParser(default_section="wily")
    config.read(config_path)

    operators = config.get(section="wily", option="operators", fallback=DEFAULT_OPERATORS)

    archiver = config.get(section="wily", option="archiver", fallback=DEFAULT_ARCHIVER)

    return WilyConfig(operators=operators, archiver=archiver)
