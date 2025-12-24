"""
Rank command.

The report command gives a table of files sorted according their ranking scheme
of a specified metric.
Will compare the values between files and return a sorted table.

TODO: Layer on Click invocation in operators section, __main__.py file
"""

import operator as op
import os
import sys
from pathlib import Path

from wily import format_date, format_revision, logger
from wily.backend import WilyIndex, find_revision, iter_filenames
from wily.cache import get_default_metrics_path
from wily.config import DEFAULT_PATH, WilyConfig
from wily.defaults import DEFAULT_ARCHIVER, DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.operators import resolve_metric_as_tuple


def rank(
    config: WilyConfig,
    path: str | None,
    metric: str,
    revision_index: str,
    limit: int,
    descending: bool,
    wrap: bool,
    table_style: str = DEFAULT_TABLE_STYLE,
) -> None:
    """
    Rank command ordering files, methods or functions using metrics.

    :param config: The configuration.
    :param path: The path to the file.
    :param metric: Name of the metric to report on.
    :param revision_index: Version of git repository to revert to.
    :param limit: Limit the number of items in the table.
    :param threshold: For total values beneath the threshold return a non-zero exit code.
    :param descending: Rank in descending order
    :param wrap: Wrap output
    :param table_style: Table box style

    :return: Sorted table of all files in path, sorted in order of metric.
    """
    logger.debug("Running rank command")

    data = []

    _operator, resolved_metric = resolve_metric_as_tuple(metric)
    operator = _operator.name
    archiver = config.archiver or DEFAULT_ARCHIVER

    # Get path to parquet index
    parquet_path = get_default_metrics_path(config, archiver)
    if not Path(parquet_path).exists():
        logger.error("Wily cache not found. Run 'wily build' first.")
        sys.exit(1)

    with WilyIndex(parquet_path, [operator]) as index:
        # Find target revision
        if not revision_index:
            # Get most recent revision
            all_rows = list(index)
            if not all_rows:
                logger.error("No data in cache. Run 'wily build' first.")
                sys.exit(1)
            all_rows.sort(key=lambda r: r.get("revision_date", 0), reverse=True)
            target_revision_key = all_rows[0]["revision"]
            target_revision_author = all_rows[0].get("revision_author", "Unknown")
            target_revision_date = all_rows[0].get("revision_date", 0)
        else:
            # Resolve revision using git
            rev_data = find_revision(config.path, revision_index)
            if not rev_data:
                logger.error("Revision %s not found.", revision_index)
                sys.exit(1)
            target_revision_key = rev_data["key"]
            target_revision_author = rev_data.get("author_name", "Unknown")
            target_revision_date = rev_data.get("date", 0)
            # Verify it's in the cache
            all_rows = list(index)
            if not any(r["revision"] == target_revision_key for r in all_rows):
                logger.error(
                    "Revision %s is not in the cache, make sure you have run wily build.",
                    revision_index,
                )
                sys.exit(1)

        logger.info(
            "-----------Rank for %s for %s by %s on %s.------------",
            resolved_metric.description,
            format_revision(target_revision_key),
            target_revision_author,
            format_date(target_revision_date),
        )

        # Build lookup of metrics for target revision: {path: metric_value}
        revision_data: dict[str, float | int | str] = {}
        for row in index:
            if row["revision"] == target_revision_key:
                file_path = row["path"]
                # Get the metric value using just the metric name (not operator.metric)
                metric_value = row.get(resolved_metric.name)
                if metric_value is not None:
                    revision_data[file_path] = metric_value

        # Filter to requested path if specified
        if path is not None:
            # Resolve target paths when the cli has specified --path
            if config.path != DEFAULT_PATH:
                targets = [str(Path(config.path) / Path(path))]
            else:
                targets = [path]

            # Expand directories to paths (normalize to Unix-style paths)
            files = [os.path.relpath(fn, config.path).replace("\\", "/") for fn in iter_filenames(targets)]
            logger.debug("Targeting - %s", files)
        else:
            # Use all files from the revision
            files = list(revision_data.keys())
            logger.debug("Analysing %s", files)

        for item in files:
            if item in revision_data:
                logger.debug(
                    "Fetching metric %s for %s in %s",
                    resolved_metric.name,
                    operator,
                    str(item),
                )
                data.append((item, revision_data[item]))
            else:
                logger.debug("Could not find file %s in index", item)

    # Sort by ideal value
    data = sorted(data, key=op.itemgetter(1), reverse=descending)

    if limit:
        data = data[:limit]

    if not data:
        return

    headers = ("File", resolved_metric.description)
    print_table(headers=headers, data=data, wrap=wrap, table_style=table_style)


