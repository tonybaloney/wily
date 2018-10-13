"""
Configuration of wily

"""

import configparser
import pathlib
import logging
from dataclasses import dataclass
from typing import Any, List


from wily.operators import OPERATOR_MCCABE
from wily.archivers import ARCHIVER_GIT

logger = logging.getLogger("wily")


@dataclass
class WilyConfig:
    operators: List
    archiver: Any
    path: str
    max_revisions: int


DEFAULT_OPERATORS = {OPERATOR_MCCABE.name}

DEFAULT_ARCHIVER = ARCHIVER_GIT.name

DEFAULT_CONFIG_PATH = "wily.cfg"

DEFAULT_CONFIG_SECTION = "wily"

DEFAULT_CACHE_PATH = ".wily"

DEFAULT_MAX_REVISIONS = 100

DEFAULT_CONFIG = WilyConfig(operators=DEFAULT_OPERATORS, archiver=DEFAULT_ARCHIVER, path=".", max_revisions=DEFAULT_MAX_REVISIONS)


def load(config_path=DEFAULT_CONFIG_PATH):
    """
    Load config file

    :return: The configuration ``WilyConfig``
    """
    if not pathlib.Path(config_path).exists():
        logger.debug(f"Could not locate {config_path}, using default config.")
        return DEFAULT_CONFIG

    config = configparser.ConfigParser(default_section=DEFAULT_CONFIG_SECTION)
    config.read(config_path)

    operators = config.get(option="operators", fallback=DEFAULT_OPERATORS)
    archiver = config.get(option="archiver", fallback=DEFAULT_ARCHIVER)
    path = config.get(option="path", fallback=".")
    max_revisions = config.get(option="max_revisions", fallback=DEFAULT_MAX_REVISIONS)

    return WilyConfig(operators=operators, archiver=archiver, path=path, max_revisions=max_revisions)
