"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""
import multiprocessing
import os
from pathlib import Path
from sys import exit
from typing import List, Optional

import radon.cli.harvest
import tabulate

from wily import format_date, format_revision, logger
from wily.archivers import resolve_archiver
from wily.commands.build import run_operator
from wily.config import DEFAULT_PATH
from wily.config.types import WilyConfig
from wily.helper import get_maxcolwidth, get_style
from wily.operators import (
    BAD_COLORS,
    GOOD_COLORS,
    OperatorLevel,
    get_metric,
    resolve_metric,
    resolve_operator,
)
from wily.state import State


def diff(
    config: WilyConfig,
    files: List[str],
    metrics: List[str],
    changes_only: bool = True,
    detail: bool = True,
    revision: Optional[str] = None,
    wrap: bool = False,
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
    files = [
        os.path.relpath(fn, config.path)
        for fn in radon.cli.harvest.iter_filenames(targets)
    ]
    logger.debug("Targeting - %s", files)

    if not revision:
        target_revision = state.index[state.default_archiver].last_revision
    else:
        rev = (
            resolve_archiver(state.default_archiver).archiver_cls(config).find(revision)
        )
        logger.debug("Resolved %s to %s (%s)", revision, rev.key, rev.message)
        try:
            target_revision = state.index[state.default_archiver][rev.key]
        except KeyError:
            logger.error(
                "Revision %s is not in the cache, make sure you have run wily build.",
                revision,
            )
            exit(1)

    logger.info(
        "Comparing current with %s by %s on %s.",
        format_revision(target_revision.revision.key),
        target_revision.revision.author_name,
        format_date(target_revision.revision.date),
    )

    # Convert the list of metrics to a list of metric instances
    operators = {resolve_operator(metric.split(".")[0]) for metric in metrics}
    resolved_metrics = [
        (metric.split(".")[0], resolve_metric(metric)) for metric in metrics
    ]
    results = []

    # Build a set of operators
    with multiprocessing.Pool(processes=len(operators)) as pool:
        operator_exec_out = pool.starmap(
            run_operator, [(operator, None, config, targets) for operator in operators]
        )
    data = {}
    for operator_name, result in operator_exec_out:
        data[operator_name] = result

    # Write a summary table
    extra = []
    for operator, metric in resolved_metrics:
        if detail and resolve_operator(operator).level == OperatorLevel.Object:
            for file in files:
                try:
                    extra.extend(
                        [
                            f"{file}:{k}"
                            for k in data[operator][file]["detailed"].keys()
                            if k != metric.name
                            and isinstance(data[operator][file]["detailed"][k], dict)
                        ]
                    )
                except KeyError:
                    logger.debug("File %s not in cache", file)
                    logger.debug("Cache follows -- ")
                    logger.debug(data[operator])
    files.extend(extra)
    logger.debug(files)
    for file in files:
        metrics_data = []
        has_changes = False
        for operator, metric in resolved_metrics:
            try:
                current = target_revision.get(
                    config, state.default_archiver, operator, file, metric.name
                )
            except KeyError:
                current = "-"
            try:
                new = get_metric(data, operator, file, metric.name)
            except KeyError:
                new = "-"
            if new != current:
                has_changes = True
            if metric.metric_type in (int, float) and new != "-" and current != "-":
                if current > new:  # type: ignore
                    metrics_data.append(
                        f"{current:n} -> \u001b[{BAD_COLORS[metric.measure]}m{new:n}\u001b[0m"
                    )
                elif current < new:  # type: ignore
                    metrics_data.append(
                        f"{current:n} -> \u001b[{GOOD_COLORS[metric.measure]}m{new:n}\u001b[0m"
                    )
                else:
                    metrics_data.append(f"{current:n} -> {new:n}")
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
        maxcolwidth = get_maxcolwidth(headers, wrap)
        style = get_style()
        print(
            # But it still makes more sense to show the newest at the top, so reverse again
            tabulate.tabulate(
                headers=headers,
                tabular_data=results,
                tablefmt=style,
                maxcolwidths=maxcolwidth,
                maxheadercolwidths=maxcolwidth,
            )
        )
