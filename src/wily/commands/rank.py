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

from wily import logger, format_revision, format_date
from wily.archivers import resolve_archiver
from wily.config import DEFAULT_GRID_STYLE, DEFAULT_PATH
from wily.state import State
from wily.operators import resolve_metric_as_tuple, MetricType

import radon.cli.harvest


def rank(config, path, metric, revision_index, limit, threshold, descending):
    """
    Rank command ordering files, methods or functions using metrics.

    :param config: The configuration
    :type config: :class:'wily.config.WilyConfig'

    :param path: The path to the file
    :type path ''str''

    :param metric: Name of the metric to report on
    :type metric: ''str''

    :param revision_index: Version of git repository to revert to.
    :type revision_index: ``str``

    :param limit: Limit the number of items in the table
    :type  limit: ``int``

    :param threshold: For total values beneath the threshold return a non-zero exit code
    :type  threshold: ``int``

    :return: Sorted table of all files in path, sorted in order of metric.
    """
    logger.debug("Running rank command")

    data = []

    operator, metric = resolve_metric_as_tuple(metric)
    operator = operator.name

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

    logger.info(
        f"-----------Rank for {metric.description} for {format_revision(target_revision.revision.key)} by {target_revision.revision.author_name} on {format_date(target_revision.revision.date)}.------------"
    )

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
        files = [
            os.path.relpath(fn, config.path)
            for fn in radon.cli.harvest.iter_filenames(targets)
        ]
        logger.debug(f"Targeting - {files}")

    for item in files:
        for archiver in state.archivers:
            try:
                logger.debug(
                    f"Fetching metric {metric.name} for {operator} in {str(item)}"
                )
                val = target_revision.get(
                    config, archiver, operator, str(item), metric.name
                )
                value = val
                data.append((item, value))
            except KeyError:
                logger.debug(f"Could not find file {item} in index")

    # Sort by ideal value
    data = sorted(data, key=op.itemgetter(1), reverse=descending)

    if limit:
        data = data[:limit]

    # Tack on the total row at the end
    total = metric.aggregate(rev[1] for rev in data)
    data.append(["Total", total])

    headers = ("File", metric.description)
    print(
        tabulate.tabulate(
            headers=headers, tabular_data=data, tablefmt=DEFAULT_GRID_STYLE
        )
    )

    if threshold and total < threshold:
        logger.error(
            f"Total value below the specified threshold: {total} < {threshold}"
        )
        exit(1)
