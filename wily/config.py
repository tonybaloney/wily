"""
Configuration of wily

"""

import configparser
from collections import namedtuple


WilyConfig = namedtuple("WilyConfig", "operators")

DEFAULT_OPERATORS = {"mccabe"}

DEFAULT_CONFIG = WilyConfig(operators=DEFAULT_OPERATORS)


def load():
    """
    Load config file

    :return: The configuration ``WilyConfig``
    """
    config = configparser.ConfigParser(default_section="wily")
    config.read('wily.cfg')

    operators = config.get(section="wily", option="operators", fallback=DEFAULT_OPERATORS)

    return WilyConfig(operators=operators)