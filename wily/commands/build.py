"""
Builds a cache based on a source-control history.

TODO : Convert .gitignore to radon ignore patterns to make the build more efficient.

"""
from progress.bar import Bar

from wily import logger
from wily.state import State

from wily.archivers.git import InvalidGitRepositoryError
from wily.archivers import FilesystemArchiver


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
    try:
        logger.debug(f"Using {archiver.name} archiver module")
        archiver = archiver.cls(config)
        revisions = archiver.revisions(config.path, config.max_revisions)
    except InvalidGitRepositoryError:
        # TODO: This logic shouldn't really be here (SoC)
        logger.info(f"Defaulting back to the filesystem archiver, not a valid git repo")
        archiver = FilesystemArchiver(config)
        revisions = archiver.revisions(config.path, config.max_revisions)
    except Exception as e:
        if hasattr(e, "message"):
            logger.error(f"Failed to setup archiver: '{e.message}'")
        else:
            logger.error(f"Failed to setup archiver: '{type(e)} - {e}'")
        exit(1)

    state = State(config, archiver=archiver)
    # Check for existence of cache, else provision
    state.ensure_exists()

    index = state.index[archiver.name]

    # remove existing revisions from the list
    revisions = [revision for revision in revisions if revision not in index]

    logger.info(
        f"Found {len(revisions)} revisions from '{archiver.name}' archiver in '{config.path}'."
    )

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info(f"Running operators - {_op_desc}")

    bar = Bar("Processing", max=len(revisions) * len(operators))
    state.operators = operators
    try:
        for revision in revisions:
            # Checkout target revision
            archiver.checkout(revision, config.checkout_options)
            # Build a set of operators
            _operators = [operator.cls(config) for operator in operators]

            stats = {"operator_data": {}}
            for operator in _operators:
                logger.debug(f"Running {operator.name} operator on {revision.key}")
                stats["operator_data"][operator.name] = operator.run(revision, config)
                bar.next()
            ir = index.add(revision, operators=operators)
            ir.store(config, archiver, stats)
        index.save()
        bar.finish()
    except Exception as e:
        logger.error(f"Failed to build cache: '{e}'")
        raise e
    finally:
        # Reset the archive after every run back to the head of the branch
        archiver.finish()
