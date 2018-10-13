"""
Builds a cache based on a source-control history
"""
import logging
import warnings

logger = logging.getLogger("wily")


def build(config, archiver, operators):
    """
    Build the history given a archiver and collection of operators.

    :param config: The wily configuration
    :type  config: :namedtuple:`wily.config.WilyConfig`

    :param archiver: The archiver to use
    :type  archiver: :namedtuple:`wily.archivers.Archiver`

    :param operators: The list of operators to execute
    :type operators: `list` of :namedtuple:`wily.operators.Operator`
    """
    archiver = archiver.cls(config)
    revisions = archiver.revisions(config.path, config.max_revisions)

    if revisions is None or len(revisions) == 0:
        logger.warn("Could not find any revisions, using HEAD")
        revisions = []  # TODO: Create a special HEAD revision to use current state
    
    # Build a set of operators
    operators = [operator.cls(config) for operator in operators]
    
    for revision in revisions:
        # Checkout target revision
        # TODO: Verify there aren't any non-committed files in working copy

        for operator in operators:
            operator.run(revision, config)

