"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""

import os
import sys
from pathlib import Path

from rich.text import Text

from wily import format_date, format_revision, logger
from wily.archivers import resolve_archiver
from wily.backend import iter_filenames
from wily.commands.build import run_operators_parallel
from wily.config import DEFAULT_PATH
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.operators import (
    BAD_STYLES,
    GOOD_STYLES,
    OperatorLevel,
    get_metric,
    resolve_metric,
    resolve_operator,
)
from wily.state import State


def diff(
    config: WilyConfig,
    files: list[str],
    metrics: list[str],
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
    state = State(config)

    # Resolve target paths when the cli has specified --path
    if config.path != DEFAULT_PATH:
        targets = [str(Path(config.path) / Path(file)) for file in files]
    else:
        targets = files

    # Expand directories to paths
    files = [os.path.relpath(fn, config.path) for fn in iter_filenames(targets)]
    logger.debug("Targeting - %s", files)

    if not revision:
        target_revision = state.index[state.default_archiver].last_revision
    else:
        rev = resolve_archiver(state.default_archiver).archiver_cls(config).find(revision)
        logger.debug("Resolved %s to %s (%s)", revision, rev.key, rev.message)
        try:
            target_revision = state.index[state.default_archiver][rev.key]
        except KeyError:
            logger.error(
                "Revision %s is not in the cache, make sure you have run wily build.",
                revision,
            )
            sys.exit(1)

    logger.info(
        "Comparing current with %s by %s on %s.",
        format_revision(target_revision.revision.key),
        target_revision.revision.author_name,
        format_date(target_revision.revision.date),
    )

    # Convert the list of metrics to a list of metric instances
    operators = {resolve_operator(metric.split(".")[0]) for metric in metrics}
    resolved_metrics = [(metric.split(".")[0], resolve_metric(metric)) for metric in metrics]
    results = []

    # Build a set of operators and run them in parallel
    data = run_operators_parallel(operators, targets, config)

    # Write a summary table
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
    for file in files:
        metrics_data: list[str | Text] = []
        has_changes = False
        for operator, metric in resolved_metrics:
            try:
                current = target_revision.get(config, state.default_archiver, operator, file, metric.name)
            except KeyError:
                current = "-"
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
