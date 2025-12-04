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
from wily.backend import WilyIndex, analyze_files_parallel, iter_filenames
from wily.cache import create as create_cache
from wily.config.types import WilyConfig
from wily.operators import Operator


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

    Used by diff command for comparing working directory changes.

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
    # This also computes directory-level aggregates
    parallel_results = analyze_files_parallel(file_paths, operator_names, multi=True)

    # Transform results into the expected format per operator
    results: dict[str, dict[str, Any]] = {name: {} for name in operator_names}

    for file_path, file_data in parallel_results.items():
        # Convert absolute paths to relative, but leave directory paths as-is
        if os.path.isabs(file_path):
            rel_path = os.path.relpath(file_path, config.path).replace("\\", "/")
        else:
            rel_path = file_path  # Already a relative/directory path from aggregation

        if "error" in file_data:
            for op_name in operator_names:
                results[op_name][rel_path] = {"total": {"error": file_data["error"]}}
            continue

        for op_name in operator_names:
            if op_name in file_data:
                results[op_name][rel_path] = file_data[op_name]

    return results


def analyze_revision_with_index(
    index: "WilyIndex",
    revision: Revision,
    archiver_instance: FilesystemArchiver,
    config: WilyConfig,
    is_seed: bool = False,
) -> int:
    """
    Analyze a revision and append results to the index.

    :param index: The WilyIndex context manager
    :param revision: The revision to analyze
    :param archiver_instance: The archiver instance
    :param config: The wily configuration
    :param is_seed: Whether this is the seed (first) revision - if True, analyze all tracked files
    :return: Total lines of code in the revision (root aggregate)
    """
    # For seed revision, analyze ALL tracked files since everything is "new"
    # For subsequent revisions, only analyze changed files
    if is_seed:
        files_to_analyze = revision.tracked_files
    else:
        files_to_analyze = revision.added_files + revision.modified_files

    targets = [
        str(pathlib.Path(config.path) / pathlib.Path(file))
        for file in files_to_analyze
    ]

    # if none of the targets are Python source files, skip analysis
    if not any(target.endswith((".py", ".ipynb")) for target in targets):
        logger.debug("Skipping analysis for revision %s, no Python files changed.", revision.key)
        return 0

    archiver_instance.checkout(revision, config.checkout_options)

    # Discover all Python files from targets
    file_paths = list(iter_filenames(targets, include_ipynb=True))

    if not file_paths:
        return 0

    logger.debug(
        "Analyzing revision %s: %d files",
        revision.key[:8],
        len(file_paths),
    )

    # Analyze and accumulate in index
    root_loc = index.analyze_revision(
        paths=file_paths,
        base_path=config.path,
        revision_key=revision.key,
        revision_date=revision.date,
        revision_author=revision.author_name,
        revision_message=revision.message,
    )

    return root_loc


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

    create_cache(config)  # Ensure cache directory exists

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

    progress_columns = (
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        SpeedColumn(),
        TimeElapsedColumn(),
    )

    # Single parquet file for all metrics
    cache_dir = pathlib.Path(config.cache_path) / archiver_instance.name
    cache_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = str(cache_dir / "metrics.parquet")
    operator_names = [op.name for op in operators]

    try:
        with Progress(*progress_columns) as progress:
            # Use WilyIndex context manager - all data written on exit
            with WilyIndex(parquet_path, operator_names) as index:
                # Revisions are returned newest-first, so we reverse to process oldest-first
                # The oldest revision (seed) should analyze ALL tracked files

                # Handle the seed revision - analyze ALL tracked files
                seed_task = progress.add_task("Analyzing seed", total=1)
                progress.start_task(seed_task)

                seed_loc = analyze_revision_with_index(
                    index, revisions[0], archiver_instance, config, is_seed=True
                )

                progress.stop_task(seed_task)
                if any(op.name == "raw" for op in operators):
                    logger.info(f"Seed revision has {seed_loc:,} lines of code.")
                logger.info("Indexed seed revision in %f seconds.", progress.tasks[seed_task].elapsed)

                # Handle the rest (oldest to newest)
                task_id = progress.add_task("Analyzing revisions", total=len(revisions) - 1)
                for revision in revisions[1:]:
                    analyze_revision_with_index(
                        index, revision, archiver_instance, config
                    )
                    progress.advance(task_id)

    except Exception as e:
        logger.error("Failed to build cache: %s: '%s'", type(e), e)
        raise e
    finally:
        archiver_instance.finish()
