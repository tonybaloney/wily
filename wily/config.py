"""
Configuration of wily

"""

import configparser
import pathlib
import logging
from dataclasses import dataclass, field
from typing import Any, List

import wily.operators as operators
from wily.archivers import ARCHIVER_GIT

logger = logging.getLogger(__name__)


@dataclass
class WilyConfig:
    operators: List
    archiver: Any
    path: str
    max_revisions: int
    targets: List[str] = None
    checkout_options: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.targets is None or '':
            self.targets = [self.path]

DEFAULT_OPERATORS = {
    operators.OPERATOR_RAW.name,
    operators.OPERATOR_MAINTAINABILITY.name,
    operators.OPERATOR_CYCLOMATIC.name,
}

DEFAULT_ARCHIVER = ARCHIVER_GIT.name

DEFAULT_CONFIG_PATH = "wily.cfg"

DEFAULT_CONFIG_SECTION = "wily"

DEFAULT_CACHE_PATH = ".wily"

DEFAULT_MAX_REVISIONS = 100

DEFAULT_CONFIG = WilyConfig(
    operators=DEFAULT_OPERATORS,
    archiver=DEFAULT_ARCHIVER,
    path=".",
    max_revisions=DEFAULT_MAX_REVISIONS,
)

DEFAULT_GRID_STYLE = 'fancy_grid'


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

    return WilyConfig(
        operators=operators, archiver=archiver, path=path, max_revisions=max_revisions
    )
