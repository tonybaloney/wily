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
    ProgressColumn,
    SpinnerColumn,
    Task,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Column
from rich.text import Text

from wily import logger
from wily.archivers import Archiver, FilesystemArchiver, Revision
from wily.archivers.git import InvalidGitRepositoryError
from wily.backend import analyze_files_parallel, iter_filenames
from wily.config.types import WilyConfig
from wily.operators import Operator, resolve_operator
from wily.state import State


class SpeedColumn(ProgressColumn):
    """Renders completed count/total and speed, e.g. '  10/1000 (5.00/sec)'."""

    def __init__(self, separator: str = "/", table_column: Column | None = None):
        """Initialize SpeedColumn."""
        self.separator = separator
        super().__init__(table_column=table_column)

    def render(self, task: "Task") -> Text:
        """Show completed/total."""
        completed = int(task.completed)
        total = int(task.total) if task.total is not None else "?"
        total_width = len(str(total))

        speed = task.speed or 0.0
        return Text(
            f"{completed:{total_width}d}{self.separator}{total} ({speed:.2f}/sec)",
            style="progress.download",
        )


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

def aggregate_values(tracked_dirs: list[str], operator_name: str, result: dict[str, dict[str, Any]]) -> None:
    """Aggregate metrics across directories."""
    dirs = [""] + [str(pathlib.Path(d)) for d in tracked_dirs if d]

    for root in sorted(dirs):
        aggregates = [p for p in result.keys() if p.startswith(root)]

        # IF nothing changed in this aggregate, don't index it.
        if not aggregates:
            continue
        result[str(root)] = {"total": {}}
        for metric in resolve_operator(operator_name).operator_cls.metrics:
            values = [
                result[agg]["total"][metric.name]
                for agg in aggregates
                if agg in result and metric.name in result[agg].get("total", {})
            ]
            if values:
                result[str(root)]["total"][metric.name] = metric.aggregate(values)

def revision_to_stats(revision: Revision, archiver_instance: FilesystemArchiver, config: WilyConfig, operators: list[Operator]) -> dict[str, dict]:
    """Convert a revision to stats by running all operators."""
    targets = [
        str(pathlib.Path(config.path) / pathlib.Path(file))
        for file in revision.added_files + revision.modified_files
    ]
    stats: dict[str, dict] = {"operator_data": {}}

    # if none of the targets are Python source files, skip analysis
    # TODO: revisit for ipynb notebooks
    if any(target.endswith(".py") for target in targets):
        archiver_instance.checkout(revision, config.checkout_options)

        # Run all operators in parallel via Rust/rayon
        results = run_operators_parallel(operators, targets, config)

        for operator_name, result in results.items():
            aggregate_values(revision.tracked_dirs, operator_name, result)
            stats["operator_data"][operator_name] = result
    else:
        logger.debug("Skipping analysis for revision %s, no Python files changed.", revision.key)
    return stats


def build(config: WilyConfig, archiver: Archiver, operators: list[Operator]) -> None:
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

    if not revisions:
        archiver_instance.finish()
        logger.debug("No new revisions to index, exiting.")
        return

    _op_desc = ",".join([operator.name for operator in operators])
    logger.info("Running operators - %s", _op_desc)

    state.operators = operators
    progress_columns = (
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        SpeedColumn(),
        TimeElapsedColumn(),
    )

    try:
        with Progress(*progress_columns) as progress:
            # Handle the seed revision
            seed_task = progress.add_task("Analyzing seed", total=1)
            progress.start_task(seed_task)
            stats = revision_to_stats(revisions[0], archiver_instance, config, operators)
            ir = index.add(revisions[0], operators=operators)
            ir.store(config, archiver_instance.name, stats)
            index.set_seed(revisions[0])
            progress.stop_task(seed_task)
            if any(op.name == "raw" for op in operators):
                loc = stats.get("operator_data", {}).get("raw", {}).get("", {}).get("total", {}).get("loc", 0)
                logger.info(f"Seed revision has {loc:,} lines of code.")
            logger.info("Indexed seed revision in %f seconds.", progress.tasks[seed_task].elapsed)

            # Handle the rest
            task_id = progress.add_task("Analyzing revisions", total=len(revisions) - 1)
            for revision in revisions[1:]:
                stats = revision_to_stats(revision, archiver_instance, config, operators)

                ir = index.add(revision, operators=operators)
                ir.store(config, archiver_instance.name, stats)
                progress.advance(task_id)

        index.save()
    except Exception as e:
        logger.error("Failed to build cache: %s: '%s'", type(e), e)
        raise e
    finally:
        archiver_instance.finish()
