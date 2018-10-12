"""
Builds a cache based on a source-control history
"""
import logging

logger = logging.getLogger("wily")


def build(config, archiver, operators):
    """

    :param config: The wily configuration
    :type  config: :namedtuple:`wily.config.WilyConfig`

    :param archiver: The archiver to use
    :type  archiver: :namedtuple:`wily.archivers.Archiver`

    :param operators: The list of operators to execute
    :type operators: `list` of :namedtuple:`wily.operators.Operator`
    """
    pass