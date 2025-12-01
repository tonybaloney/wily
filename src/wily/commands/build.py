"""
Builds a cache based on a source-control history.

TODO : Convert .gitignore to radon ignore patterns to make the build more efficient.

"""

import os
import pathlib
import sys
from typing import Any

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from wily import logger
from wily.archivers import Archiver, FilesystemArchiver, Revision
from wily.archivers.git import InvalidGitRepositoryError
from wily.backend import analyze_files_parallel, iter_filenames
from wily.config.types import WilyConfig
from wily.operators import Operator, resolve_operator
from wily.state import State


def run_operators_parallel(
    operators: list[Operator],
    targets: list[str],
    config: WilyConfig,
) -> dict[str, dict[str, Any]]:
    """
    Run all operators in parallel using Rust/rayon.

    :param operators: List of operators to run
    :param targets: List of file paths to analyze
    :param config: The wily configuration
    :return: Dictionary mapping operator names to their results
    """
    operator_names = [op.name for op in operators]

    if not operator_names or not targets:
        return {name: {} for name in operator_names}

    # Discover all Python files from targets
    file_paths = list(iter_filenames(targets, include_ipynb=True))

    if not file_paths:
        return {name: {} for name in operator_names}

    logger.debug(
        "Running Rust parallel analysis on %d files with operators: %s",
        len(file_paths),
        operator_names,
    )

    # Run all operators in parallel on all files using Rust/rayon
    parallel_results = analyze_files_parallel(file_paths, operator_names, multi=True)

    # Transform results into the expected format per operator
    results: dict[str, dict[str, Any]] = {name: {} for name in operator_names}

    for file_path, file_data in parallel_results.items():
        rel_path = os.path.relpath(file_path, config.path)

        if "error" in file_data:
            for op_name in operator_names:
                results[op_name][rel_path] = {"total": {"error": file_data["error"]}}
            continue

        for op_name in operator_names:
            if op_name in file_data:
                results[op_name][rel_path] = file_data[op_name]

    return results


def build(config: WilyConfig, archiver: Archiver, operators: list[Operator], diff: bool = True) -> None:
    """
    Build the history given an archiver and collection of operators.

    :param config: The wily configuration
    :param archiver: The archiver to use
    :param operators: The list of operators to execute
    :param diff: Only store diffs in revisions (default True)
    """
    try:
        logger.debug("Using %s archiver module", archiver.name)
        archiver_instance = archiver.archiver_cls(config)
        revisions = archiver_instance.revisions(config.path, config.max_revisions)
    except InvalidGitRepositoryError:
        logger.info("Defaulting back to the filesystem archiver, not a valid git repo")
        archiver_instance = FilesystemArchiver(config)
        revisions = archiver_instance.revisions(config.path, config.max_revisions)
    except Exception as e:
        message = getattr(e, "message", f"{type(e)} - {e}")
        logger.error("Failed to setup archiver: '%s'", message)
        sys.exit(1)

    state = State(config, archiver=archiver_instance)
    state.ensure_exists()

    index = state.index[archiver_instance.name]
    revisions = [revision for revision in revisions if revision not in index][::-1]

    logger.info(
        "Found %s revisions from '%s' archiver in '%s'.",
        len(revisions),
        archiver_instance.name,
        config.path,
    )

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info("Running operators - %s", _op_desc)

    state.operators = operators
    progress_columns = (
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(show_speed=True),
        TimeElapsedColumn(),
    )

    seed: Revision | None = None
    try:
        with Progress(*progress_columns) as progress:
            task_id = progress.add_task("Processing", total=len(revisions))
            prev_stats: dict[str, dict] = {}

            for revision in revisions:
                if not seed:
                    seed = revision

                archiver_instance.checkout(revision, config.checkout_options)
                stats: dict[str, dict] = {"operator_data": {}}

                targets = [
                    str(pathlib.Path(config.path) / pathlib.Path(file))
                    for file in revision.added_files + revision.modified_files
                ]

                # Run all operators in parallel via Rust/rayon
                results = run_operators_parallel(operators, targets, config)

                for operator_name, result in results.items():
                    indices = set(result.keys())

                    # Copy data from unchanged files from previous revision
                    if not diff and seed is revision:
                        files = {str(pathlib.Path(f)) for f in revision.tracked_files}
                        missing_indices = files - indices
                        for missing in missing_indices:
                            if missing in revision.tracked_dirs:
                                continue
                            if operator_name not in prev_stats["operator_data"]:
                                continue
                            if missing not in prev_stats["operator_data"][operator_name]:
                                continue
                            result[missing] = prev_stats["operator_data"][operator_name][missing]
                        for deleted in revision.deleted_files:
                            result.pop(deleted, None)

                    # Aggregate metrics across directories
                    dirs = [""] + [str(pathlib.Path(d)) for d in revision.tracked_dirs if d]
                    for root in sorted(dirs):
                        aggregates = [p for p in result.keys() if p.startswith(root)]
                        result[str(root)] = {"total": {}}
                        for metric in resolve_operator(operator_name).operator_cls.metrics:
                            values = [
                                result[agg]["total"][metric.name]
                                for agg in aggregates
                                if agg in result and metric.name in result[agg].get("total", {})
                            ]
                            if values:
                                result[str(root)]["total"][metric.name] = metric.aggregate(values)

                    stats["operator_data"][operator_name] = result

                prev_stats = stats
                ir = index.add(revision, operators=operators)
                ir.store(config, archiver_instance.name, stats)
                progress.advance(task_id)
            if seed:
                index.set_seed(seed)
            index.save()
    except Exception as e:
        logger.error("Failed to build cache: %s: '%s'", type(e), e)
        raise e
    finally:
        archiver_instance.finish()
