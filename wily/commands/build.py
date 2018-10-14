"""
Builds a cache based on a source-control history
"""
import progressbar

from wily import logger
import wily.cache as cache


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
        logger.debug("Wily cache not found, creating.")
        cache.create()
        logger.debug("Created wily cache")

    logger.debug(f"Using {archiver.name} archiver module")
    archiver = archiver.cls(config)

    revisions = archiver.revisions(config.path, config.max_revisions)
    logger.info(
        f"Found {len(revisions)} revisions from '{archiver.name}' archiver in {config.path}."
    )

    if revisions is None or len(revisions) == 0:
        logger.warning("Could not find any revisions, using HEAD")
        revisions = []  # TODO: Create a special HEAD revision to use current state

    # Build a set of operators
    operators = [operator.cls(config) for operator in operators]

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info(f"Running operators - {_op_desc}")

    with progressbar.ProgressBar(max_value=config.max_revisions*len(operators), redirect_stdout=True) as bar:
        i = 0
        try:
            for revision in revisions:
                # Checkout target revision
                archiver.checkout(revision, config.checkout_options)

                stats = {
                    "revision": revision.key,
                    "author_name": revision.author_name,
                    "author_email": revision.author_email,
                    "date": revision.revision_date,
                    "operator_data": {},
                }
                for operator in operators:
                    logger.debug(f"Running {operator.name} operator on {revision.key}")
                    stats["operator_data"][operator.name] = operator.run(revision, config)
                cache.store(archiver, revision, stats)
                bar.update(i)
                i += 1
        finally:
            # Reset the archive after every run back to the head of the branch
            archiver.finish()
