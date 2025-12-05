"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""

import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from rich.text import Text

from wily import logger
from wily.backend import WilyIndex, iter_filenames
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


def diff(  # noqa: C901
    config: WilyConfig,
    files: list[str],
    metrics: list[str] | None,
    changes_only: bool = True,
    detail: bool = True,
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
    last_data: dict[str, dict[str, Any]] = defaultdict(dict)
    # Load the index and find target revision
    with WilyIndex(parquet_path, operator_names) as index:
        # Build lookup of cached metrics for target revision: {path: {metric: value}}
        for file in files:
            for row in index[file]:
                # Copy all metric values
                for key, value in row.items():
                    if key not in ("revision", "revision_date", "revision_author", "revision_message", "path", "path_type"):
                        last_data[file][key] = value
                break

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
                current = last_data.get(file, {}).get(metric.name, "-")
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
