"""
Rank command.

The report command gives a table of files sorted according their ranking scheme
of a specified metric.
Will compare the values between files and return a sorted table.

TODO: Layer on Click invocation in operators section, __main__.py file
"""
import os

import tabulate
import operator as op
from pathlib import Path

from wily import logger, format_date, format_revision
from wily.archivers import resolve_archiver
from wily.config import DEFAULT_GRID_STYLE, DEFAULT_PATH
from wily.operators import resolve_metric, MetricType
from wily.state import State

import radon.cli.harvest


def aggregate_metric(metric_table: list):
    """
    Aggregate/total wily metrics in a tabular format.

    Data is assumed to be in the tabular format of the rank function within the rank.py
    command.

    :param metric_table: table with list of wily metrics across multiple files.
    :type metric_table: ''list''

    :return: Sorted table of all files in path, sorted in order of metric.
    """
    # value in first draft is assumed to be the fifth item in the list.
    return ["Total", "---", "---", "---", sum(float(rev[4]) for rev in metric_table)]


def rank(config, path, metric, revision_index):
    """
    Rank command ordering files, methods or functions using metrics.

    :param config: The configuration
    :type config: :class:'wily.config.WilyConfig'

    :param path: The path to the file
    :type path ''str''

    :param metric: Name of the metric to report on
    :type metric: ''str''

    :param revision_index: Version of git repository to revert to.
    :type revision_index: ''int''

    :return: Sorted table of all files in path, sorted in order of metric.
    """
    logger.debug("Running rank command")
    logger.info(f"-----------Rank for {metric}------------")

    data = []

    operator, key = metric.split(".")
    metric = resolve_metric(metric)
    metric_meta = {
        "key": key,
        "operator": operator,
        "title": metric.description,
        "type": metric.type,
        "wily_metric_type": metric.measure.name,  # AimHigh, AimLow, Informational
    }

    state = State(config)

    if not revision_index:
        target_revision = state.index[state.default_archiver].last_revision
    else:
        rev = resolve_archiver(state.default_archiver).cls(config).find(revision_index)
        logger.debug(f"Resolved {revision_index} to {rev.key} ({rev.message})")
        try:
            target_revision = state.index[state.default_archiver][rev.key]
        except KeyError:
            logger.error(
                f"Revision {revision_index} is not in the cache, make sure you have run wily build."
            )
            exit(1)

    if path is None:
        files = target_revision.get_paths(config, state.default_archiver, operator)
        logger.debug(f"Analysing {files}")
    else:
        # Resolve target paths when the cli has specified --path
        if config.path != DEFAULT_PATH:
            targets = [str(Path(config.path) / Path(path))]
        else:
            targets = [path]

        # Expand directories to paths
        files = [os.path.relpath(fn, config.path) for fn in radon.cli.harvest.iter_filenames(targets)]
        logger.debug(f"Targeting - {files}")

    for item in files:
        for archiver in state.archivers:
            try:
                logger.debug(
                    f"Fetching metric {metric_meta['key']} for {metric_meta['operator']} in {str(item)}"
                )
                val = target_revision.get(
                    config,
                    archiver,
                    metric_meta["operator"],
                    str(item),
                    metric_meta["key"],
                )
                value = str(val)
                data.append(
                    (
                        item,
                        format_revision(target_revision.revision.key),
                        target_revision.revision.author_name,
                        format_date(target_revision.revision.date),
                        value,
                    )
                )
            except KeyError:
                logger.debug(f"Could not find file {item} in index")

    # Sort by ideal value
    if metric_meta["wily_metric_type"] == "AimHigh":
        # AimHigh is sorted lowest to highest
        data.sort(key=op.itemgetter(4))
    elif metric_meta["wily_metric_type"] == "AimLow":
        # AimLow is sorted highest to lowest
        data.sort(key=op.itemgetter(4), reverse=True)
    # Tack on the total row at the end
    data.append(aggregate_metric(data))

    headers = ("File", "Revision", "Last Author", "Date", metric_meta["title"])
    print(
        tabulate.tabulate(
            headers=headers, tabular_data=data, tablefmt=DEFAULT_GRID_STYLE
        )
    )
