"""
Builds a cache based on a source-control history.

TODO : Convert .gitignore to radon ignore patterns to make the build more efficient.

"""
import multiprocessing
import os
import pathlib
from sys import exit

from progress.bar import Bar

from wily import logger
from wily.archivers import FilesystemArchiver
from wily.archivers.git import InvalidGitRepositoryError
from wily.operators import resolve_operator
from wily.state import State


def run_operator(operator, revision, config, targets):
    """
    Run an operator for the multiprocessing pool.

    :param operator: The operator to use
    :type  operator: :class:`Operator`

    :param revision: The revision index
    :type  revision: :class:`Revision`

    :param config: The runtime configuration
    :type  config: :class:`WilyConfig`

    :param targets: Files/paths to scan
    :type  targets: ``list`` of ``str``

    :rtype: ``tuple``
    :returns: A tuple of operator name (``str``), and data (``dict``)
    """
    instance = operator.cls(config, targets)
    logger.debug(f"Running {operator.name} operator on {revision}")

    data = instance.run(revision, config)

    # Normalize paths for non-seed passes
    for key in list(data.keys()):
        if os.path.isabs(key):
            rel = os.path.relpath(key, config.path)
            data[rel] = data[key]
            del data[key]

    return operator.name, data


def build(config, archiver, operators):
    """
    Build the history given an archiver and collection of operators.

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
        logger.info("Defaulting back to the filesystem archiver, not a valid git repo")
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
    revisions = [revision for revision in revisions if revision not in index][::-1]

    logger.info(
        f"Found {len(revisions)} revisions from '{archiver.name}' archiver in '{config.path}'."
    )

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info(f"Running operators - {_op_desc}")

    bar = Bar("Processing", max=len(revisions) * len(operators))
    state.operators = operators

    # Index all files the first time, only scan changes afterward
    seed = True
    try:
        with multiprocessing.Pool(processes=len(operators)) as pool:
            for revision in revisions:
                # Checkout target revision
                archiver.checkout(revision, config.checkout_options)
                stats = {"operator_data": {}}

                # TODO : Check that changed files are children of the targets
                targets = [
                    str(pathlib.Path(config.path) / pathlib.Path(file))
                    for file in revision.added_files + revision.modified_files
                    # if any([True for target in config.targets if
                    #         target in pathlib.Path(pathlib.Path(config.path) / pathlib.Path(file)).parents])
                ]

                # Run each operator as a separate process
                data = pool.starmap(
                    run_operator,
                    [(operator, revision, config, targets) for operator in operators],
                )
                # data is a list of tuples, where for each operator, it is a tuple of length 2,
                operator_data_len = 2
                # second element in the tuple, i.e data[i][1]) has the collected data
                for i in range(0, len(operators)):
                    if (
                        i < len(data)
                        and len(data[i]) >= operator_data_len
                        and len(data[i][1]) == 0
                    ):
                        logger.warning(
                            f"In revision {revision.key}, for operator {operators[i].name}: No data collected"
                        )

                # Map the data back into a dictionary
                for operator_name, result in data:
                    # find all unique directories in the results
                    indices = set(result.keys())

                    # For a seed run, there is no previous change set, so use current
                    if seed:
                        prev_indices = indices

                    # Copy the ir from any unchanged files from the prev revision
                    if not seed:
                        missing_indices = set(revision.tracked_files) - indices
                        # TODO: Check existence of file path.
                        for missing in missing_indices:
                            # Don't copy aggregate keys as their values may have changed
                            if missing in revision.tracked_dirs:
                                continue
                            # previous index may not have that operator
                            if operator_name not in prev_stats["operator_data"]:
                                continue
                            # previous index may not have file either
                            if (
                                missing
                                not in prev_stats["operator_data"][operator_name]
                            ):
                                continue
                            result[missing] = prev_stats["operator_data"][
                                operator_name
                            ][missing]
                        for deleted in revision.deleted_files:
                            result.pop(deleted, None)

                    # Aggregate metrics across all root paths using the aggregate function in the metric
                    # Note assumption is that nested dirs are listed after parent..
                    for root in revision.tracked_dirs:
                        # find all matching entries recursively
                        aggregates = [
                            path for path in result.keys() if path.startswith(root)
                        ]

                        result[str(root)] = {"total": {}}
                        # aggregate values
                        for metric in resolve_operator(operator_name).cls.metrics:
                            func = metric.aggregate
                            values = [
                                result[aggregate]["total"][metric.name]
                                for aggregate in aggregates
                                if aggregate in result
                                and metric.name in result[aggregate]["total"]
                            ]
                            if len(values) > 0:
                                result[str(root)]["total"][metric.name] = func(values)

                    prev_indices = set(result.keys())
                    stats["operator_data"][operator_name] = result
                    bar.next()

                prev_stats = stats
                seed = False
                ir = index.add(revision, operators=operators)
                ir.store(config, archiver, stats)
        index.save()
        bar.finish()
    except Exception as e:
        logger.error(f"Failed to build cache: {type(e)}: '{e}'")
        raise e
    finally:
        # Reset the archive after every run back to the head of the branch
        archiver.finish()
