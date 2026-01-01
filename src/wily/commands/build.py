"""
Builds a cache based on a source-control history.

TODO : Convert .gitignore to radon ignore patterns to make the build more efficient.

"""
from datetime import datetime

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
from wily.archivers import Archiver, FilesystemArchiver, RevisionInfo
from wily.archivers.git import GitArchiver, InvalidGitRepositoryError
from wily.backend import WilyIndex
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


def analyze_revision_with_index(
    index: "WilyIndex",
    revision: RevisionInfo,
    archiver_instance: FilesystemArchiver | GitArchiver,
    config: WilyConfig,
) -> int:
    """
    Analyze a revision and append results to the index.

    :param index: The WilyIndex context manager
    :param revision: The revision to analyze
    :param archiver_instance: The archiver instance
    :param config: The wily configuration
    :return: Total lines of code in the revision (root aggregate)
    """
    if not revision["added_files"] and not revision["modified_files"]:
        # Skip this version
        return 0

    archiver_instance.checkout(revision, config.checkout_options)

    # Analyze and accumulate in index
    return index.analyze_revision(
        paths=revision["added_files"] + revision["modified_files"],
        base_path=config.path,
        revision_key=revision["key"],
        revision_date=revision["date"],
        revision_author=revision["author_name"],
        revision_message=revision["message"],
    )


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
                for i, revision in enumerate(revisions):
                    if i == 0:
                        seed_task = progress.add_task("Analyzing seed", total=1)
                        progress.start_task(seed_task)

                        seed_loc = analyze_revision_with_index(
                            index, revision, archiver_instance, config
                        )

                        progress.stop_task(seed_task)
                        if any(op.name == "raw" for op in operators):
                            logger.info(f"Seed revision has {seed_loc:,} lines of code.")
                        logger.info("Indexed seed revision in %f seconds.", progress.tasks[seed_task].elapsed)
                        continue
                    elif i == 1:
                        task_id = progress.add_task("Analyzing revisions", total=len(revisions) - 1)

                    analyze_revision_with_index(
                        index, revision, archiver_instance, config
                    )
                    progress.advance(task_id) # type: ignore

    except Exception as e:
        logger.error("Failed to build cache: %s: '%s'", type(e), e)
        raise e
    finally:
        archiver_instance.finish()
