"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""

import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from rich.text import Text

from wily import format_date, format_revision, logger
from wily.backend import WilyIndex, find_revision, iter_filenames
from wily.cache import get_default_metrics_path
from wily.commands.build import run_operators_parallel
from wily.config import DEFAULT_PATH
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_ARCHIVER, DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.operators import (
    ALL_METRICS,
    ALL_OPERATORS,
    BAD_STYLES,
    GOOD_STYLES,
    Metric,
    Operator,
    OperatorLevel,
    get_metric,
    resolve_metric,
    resolve_operator,
)


def diff(
    config: WilyConfig,
    files: list[str],
    metrics: list[str] | None,
    changes_only: bool = True,
    detail: bool = True,
    revision: str | None = None,
    wrap: bool = False,
    table_style: str = DEFAULT_TABLE_STYLE,
) -> None:
    """
    Show the differences in metrics for each of the files.

    :param config: The wily configuration
    :param files: The files to compare.
    :param metrics: The metrics to measure.
    :param changes_only: Only include changes files in output.
    :param detail: Show details (function-level)
    :param revision: Compare with specific revision
    :param wrap: Wrap output
    :param table_style: Table box style
    """
    config.targets = files
    files = list(files)
    archiver = config.archiver or DEFAULT_ARCHIVER

    # Resolve target paths when the cli has specified --path
    if config.path != DEFAULT_PATH:
        targets = [str(Path(config.path) / Path(file)) for file in files]
    else:
        targets = files

    # Expand directories to paths (normalize to Unix-style paths)
    files = [os.path.relpath(fn, config.path).replace("\\", "/") for fn in iter_filenames(targets)]
    logger.debug("Targeting - %s", files)

    # Get path to parquet index
    parquet_path = get_default_metrics_path(config, archiver)
    if not Path(parquet_path).exists():
        logger.error("Wily cache not found. Run 'wily build' first.")
        sys.exit(1)

    # Determine operators from config or metrics
    operators: list[Operator]
    resolved_metrics: Iterable[tuple[str, Metric]]
    if metrics:
        operators = [resolve_operator(metric.split(".")[0]) for metric in metrics]
        resolved_metrics = [(metric.split(".")[0], resolve_metric(metric)) for metric in metrics]
    else:
        operators = list(ALL_OPERATORS.values())
        resolved_metrics = [(operator.name, metric) for operator, metric in ALL_METRICS if operator in operators]

    operator_names = [op.name for op in operators]

    # Load the index and find target revision
    with WilyIndex(parquet_path, operator_names) as index:
        # Find the target revision to compare against
        if not revision:
            # Get the most recent revision from the index
            all_rows = list(index)
            if not all_rows:
                logger.error("No data in cache. Run 'wily build' first.")
                sys.exit(1)
            # Sort by date descending to get most recent
            all_rows.sort(key=lambda r: r.get("revision_date", 0), reverse=True)
            target_revision_key = all_rows[0]["revision"]
            target_revision_author = all_rows[0].get("revision_author", "Unknown")
            target_revision_date = all_rows[0].get("revision_date", 0)
        else:
            # Resolve revision using git
            rev_data = find_revision(config.path, revision)
            if not rev_data:
                logger.error("Revision %s not found in git.", revision)
                sys.exit(1)
            target_revision_key = rev_data["key"]
            target_revision_author = rev_data.get("author_name", "Unknown")
            target_revision_date = rev_data.get("date", 0)
            # Verify it's in the cache
            all_rows = list(index)
            if not any(r["revision"] == target_revision_key for r in all_rows):
                logger.error(
                    "Revision %s is not in the cache, make sure you have run wily build.",
                    revision,
                )
                sys.exit(1)

        logger.info(
            "Comparing current with %s by %s on %s.",
            format_revision(target_revision_key),
            target_revision_author,
            format_date(target_revision_date),
        )

        # Build lookup of cached metrics for target revision: {path: {metric: value}}
        cached_data: dict[str, dict[str, Any]] = {}
        for row in index:
            if row["revision"] == target_revision_key:
                path = row["path"]
                if path not in cached_data:
                    cached_data[path] = {}
                # Copy all metric values
                for key, value in row.items():
                    if key not in ("revision", "revision_date", "revision_author", "revision_message", "path", "path_type"):
                        cached_data[path][key] = value

    # Run operators on current files
    data = run_operators_parallel(operators, targets, config)

    # Build list of extra paths (functions/classes) from current data
    extra = []
    for operator, metric in resolved_metrics:
        if detail and resolve_operator(operator).level == OperatorLevel.Object:
            for file in files:
                try:
                    extra.extend([f"{file}:{k}" for k in data[operator][file]["detailed"].keys() if k != metric.name and isinstance(data[operator][file]["detailed"][k], dict)])
                except KeyError:
                    logger.debug("File %s not in cache", file)
                    logger.debug("Cache follows -- ")
                    logger.debug(data[operator])

    files.extend(extra)
    logger.debug(files)

    results = []
    for file in files:
        metrics_data: list[str | Text] = []
        has_changes = False
        for operator, metric in resolved_metrics:
            # Get cached value for this file/metric (parquet stores just metric name, not operator.metric)
            try:
                current = cached_data.get(file, {}).get(metric.name, "-")
                if current is None:
                    current = "-"
            except KeyError:
                current = "-"
            # Get new value from current analysis
            try:
                new = get_metric(data, operator, file, metric.name)
            except KeyError:
                new = "-"
            if new != current:
                has_changes = True
            if metric.metric_type in (int, float) and new != "-" and current != "-":
                cell = Text(f"{current:n} -> ")
                if current > new:  # type: ignore
                    cell.append(f"{new:n}", style=BAD_STYLES[metric.measure])
                elif current < new:  # type: ignore
                    cell.append(f"{new:n}", style=GOOD_STYLES[metric.measure])
                else:
                    cell.append(f"{new:n}")
                metrics_data.append(cell)
            else:
                if current == "-" and new == "-":
                    metrics_data.append("-")
                else:
                    metrics_data.append(f"{current} -> {new}")
        if has_changes or not changes_only:
            results.append((file, *metrics_data))
        else:
            logger.debug(metrics_data)

    descriptions = [metric.description for _, metric in resolved_metrics]
    headers = ("File", *descriptions)
    if len(results) > 0:
        print_table(headers=headers, data=results, wrap=wrap, table_style=table_style)
