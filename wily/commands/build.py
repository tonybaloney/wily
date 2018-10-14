"""
Builds a cache based on a source-control history
"""
import wily.cache as cache
import logging

logger = logging.getLogger(__name__)


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
    # Check for existence of cache, else provision
    if not cache.exists():
        logging.debug("Wily cache not found, creating.")
        cache.create()
        logging.debug("Created wily cache")

    logging.debug(f"Using {archiver.name} archiver module")
    archiver = archiver.cls(config)

    revisions = archiver.revisions(config.path, config.max_revisions)
    logging.info(f"Found {len(revisions)} revisions")

    if revisions is None or len(revisions) == 0:
        logger.warning("Could not find any revisions, using HEAD")
        revisions = []  # TODO: Create a special HEAD revision to use current state

    # Build a set of operators
    operators = [operator.cls(config) for operator in operators]

    try:
        for revision in revisions:
            # Checkout target revision
            archiver.checkout(revision, config.checkout_options)

            stats = {}
            for operator in operators:
                logging.debug(f"Running {operator} on {revision}")
                stats[operator.name] = operator.run(revision, config)
            cache.store(archiver, revision, stats)
    finally:
        # Reset the archive after every run back to the head of the branch
        archiver.finish()
