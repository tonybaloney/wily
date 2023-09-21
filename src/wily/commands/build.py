"""
Builds a cache based on a source-control history.

TODO : Convert .gitignore to radon ignore patterns to make the build more efficient.

"""
import multiprocessing
import os
import pathlib
from sys import exit
from typing import Any, Dict, List, Tuple

from progress.bar import Bar

from wily import logger
from wily.archivers import Archiver, FilesystemArchiver, Revision
from wily.archivers.git import InvalidGitRepositoryError
from wily.config.types import WilyConfig
from wily.operators import Operator, resolve_operator
from wily.state import State


def run_operator(
    operator: Operator, revision: Revision, config: WilyConfig, targets: List[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Run an operator for the multiprocessing pool.

    :param operator: The operator to use
    :param revision: The revision index
    :param config: The runtime configuration
    :param targets: Files/paths to scan
    """
    instance = operator.operator_cls(config, targets)
    logger.debug("Running %s operator on %s", operator.name, revision)

    data = instance.run(revision, config)

    # Normalize paths for non-seed passes
    for key in list(data.keys()):
        if os.path.isabs(key):
            rel = os.path.relpath(key, config.path)
            data[rel] = data[key]
            del data[key]

    return operator.name, data


def build(config: WilyConfig, archiver: Archiver, operators: List[Operator]) -> None:
    """
    Build the history given an archiver and collection of operators.

    :param config: The wily configuration
    :param archiver: The archiver to use
    :param operators: The list of operators to execute
    """
    try:
        logger.debug("Using %s archiver module", archiver.name)
        archiver_instance = archiver.archiver_cls(config)
        revisions = archiver_instance.revisions(config.path, config.max_revisions)
    except InvalidGitRepositoryError:
        # TODO: This logic shouldn't really be here (SoC)
        logger.info("Defaulting back to the filesystem archiver, not a valid git repo")
        archiver_instance = FilesystemArchiver(config)
        revisions = archiver_instance.revisions(config.path, config.max_revisions)
    except Exception as e:
        message = getattr(e, "message", f"{type(e)} - {e}")
        logger.error("Failed to setup archiver: '%s'", message)
        exit(1)

    state = State(config, archiver=archiver_instance)
    # Check for existence of cache, else provision
    state.ensure_exists()

    index = state.index[archiver_instance.name]

    # remove existing revisions from the list
    revisions = [revision for revision in revisions if revision not in index][::-1]

    logger.info(
        "Found %s revisions from '%s' archiver in '%s'.",
        len(revisions),
        archiver_instance.name,
        config.path,
    )

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info("Running operators - %s", _op_desc)

    bar = Bar("Processing", max=len(revisions) * len(operators))
    state.operators = operators

    # Index all files the first time, only scan changes afterward
    seed = True
    try:
        with multiprocessing.Pool(processes=len(operators)) as pool:
            prev_stats: Dict[str, Dict] = {}
            for revision in revisions:
                # Checkout target revision
                archiver_instance.checkout(revision, config.checkout_options)
                stats: Dict[str, Dict] = {"operator_data": {}}

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
                            "In revision %s, for operator %s: No data collected",
                            revision.key,
                            operators[i].name,
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
                        # File names in result are platform dependent, so we convert
                        # to Path and back to str.
                        files = {str(pathlib.Path(f)) for f in revision.tracked_files}
                        missing_indices = files - indices
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

                    # Add empty path for storing total aggregates
                    dirs = [""]
                    # Directory names in result are platform dependent, so we convert
                    # to Path and back to str.
                    dirs += [str(pathlib.Path(d)) for d in revision.tracked_dirs if d]
                    # Aggregate metrics across all root paths using the aggregate function in the metric
                    # Note assumption is that nested dirs are listed after parent, hence sorting.
                    for root in sorted(dirs):
                        # find all matching entries recursively
                        aggregates = [
                            path for path in result.keys() if path.startswith(root)
                        ]

                        result[str(root)] = {"total": {}}
                        # aggregate values
                        for metric in resolve_operator(
                            operator_name
                        ).operator_cls.metrics:
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
                ir.store(config, archiver_instance.name, stats)
        index.save()
        bar.finish()
    except Exception as e:
        logger.error("Failed to build cache: %s: '%s'", type(e), e)
        raise e
    finally:
        # Reset the archive after every run back to the head of the branch
        archiver_instance.finish()
