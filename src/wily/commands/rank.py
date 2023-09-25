"""
Rank command.

The report command gives a table of files sorted according their ranking scheme
of a specified metric.
Will compare the values between files and return a sorted table.

TODO: Layer on Click invocation in operators section, __main__.py file
"""
import operator as op
import os
from pathlib import Path
from sys import exit
from typing import Optional

import radon.cli.harvest
import tabulate

from wily import format_date, format_revision, logger
from wily.archivers import resolve_archiver
from wily.config import DEFAULT_PATH, WilyConfig
from wily.helper import get_maxcolwidth, get_style
from wily.operators import resolve_metric_as_tuple
from wily.state import State


def rank(
    config: WilyConfig,
    path: Optional[str],
    metric: str,
    revision_index: str,
    limit: int,
    threshold: int,
    descending: bool,
    wrap: bool,
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

    :return: Sorted table of all files in path, sorted in order of metric.
    """
    logger.debug("Running rank command")

    data = []

    _operator, resolved_metric = resolve_metric_as_tuple(metric)
    operator = _operator.name

    state = State(config)

    if not revision_index:
        target_revision = state.index[state.default_archiver].last_revision
    else:
        rev = (
            resolve_archiver(state.default_archiver)
            .archiver_cls(config)
            .find(revision_index)
        )
        logger.debug("Resolved %s to %s (%s)", revision_index, rev.key, rev.message)
        try:
            target_revision = state.index[state.default_archiver][rev.key]
        except KeyError:
            logger.error(
                "Revision %s is not in the cache, make sure you have run wily build.",
                revision_index,
            )
            exit(1)

    logger.info(
        "-----------Rank for %s for %s by %s on %s.------------",
        resolved_metric.description,
        format_revision(target_revision.revision.key),
        target_revision.revision.author_name,
        format_date(target_revision.revision.date),
    )

    if path is None:
        files = target_revision.get_paths(config, state.default_archiver, operator)
        logger.debug("Analysing %s", files)
    else:
        # Resolve target paths when the cli has specified --path
        if config.path != DEFAULT_PATH:
            targets = [str(Path(config.path) / Path(path))]
        else:
            targets = [path]

        # Expand directories to paths
        files = [
            os.path.relpath(fn, config.path)
            for fn in radon.cli.harvest.iter_filenames(targets)
        ]
        logger.debug("Targeting - %s", files)

    for item in files:
        for archiver in state.archivers:
            try:
                logger.debug(
                    "Fetching metric %s for %s in %s",
                    resolved_metric.name,
                    operator,
                    str(item),
                )
                val = target_revision.get(
                    config, archiver, operator, str(item), resolved_metric.name
                )
                value = val
                data.append((item, value))
            except KeyError:
                logger.debug("Could not find file %s in index", item)

    # Sort by ideal value
    data = sorted(data, key=op.itemgetter(1), reverse=descending)

    if limit:
        data = data[:limit]

    if not data:
        return

    # Tack on the total row at the end
    total = resolved_metric.aggregate(rev[1] for rev in data)
    data.append(("Total", total))

    headers = ("File", resolved_metric.description)
    maxcolwidth = get_maxcolwidth(headers, wrap)
    style = get_style()
    print(
        tabulate.tabulate(
            headers=headers,
            tabular_data=data,
            tablefmt=style,
            maxcolwidths=maxcolwidth,
            maxheadercolwidths=maxcolwidth,
        )
    )

    if threshold and total < threshold:
        logger.error(
            "Total value below the specified threshold: %s < %s", total, threshold
        )
        exit(1)
