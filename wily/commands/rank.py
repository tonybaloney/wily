"""
Rank command.

The report command gives a table of files sorted according their ranking scheme
of a specified metric.
Will compare the values between files and return a sorted table.


TODO: Refactor individual file work into a separate function
TODO: Layer on Click invocation in operators section, __main__.py file
TODO: Is the a better way to retrieve the revision number than via index?
"""
import tabulate
import os
import operator as op

from wily import logger, format_date, format_revision, MAX_MESSAGE_WIDTH
from wily.config import DEFAULT_GRID_STYLE
from wily.operators import resolve_metric, MetricType
from wily.state import State


def rank(config, path, metric="maintainability.index", revision_number=0):
    """

    :param config: The configuration
    :type config: :class:'wily.config.WilyConfig'

    :param path: The path to the file
    :type path ''str''

    :param metric: Name of the metric to report on
    :type metric: ''str''

    :param revision_number: Version of git repository to revert to.
    :type revision_number: ''int''

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

    # vals = []
    # Assumption is there is only one metric (e.g., therefore list of metrics commented out)
    items = os.listdir(path)
    for item in items:
        full_item = os.path.join(path, item)
        if os.path.isdir(full_item):
            continue  #  sub-folders are ignored in first draft of rank
        elif os.path.isfile(full_item):
            state = State(config)
            for archiver in state.archivers:
                # Last revision in the list is the first item (ordered Newest to Oldest => 0 to -1 index.
                rev = state.index[archiver].revisions[revision_number]
                for meta in metric_meta:
                    try:
                        logger.debug(
                            f"Fetching metric {meta['key']} for {meta['operator']} in {path}"
                            )
                        val = rev.get(config, archiver, meta["operator"], path, meta["key"])
                        value = f"{val}"
                    except KeyError as e:
                        value = f"Not found {e}"
                    # vals.append(k)
                    # Assumption is there is only one metric (e.g., value versus val* as in report.py command
                    data.append(
                        (
                            # wonder if revision specific information should be in here given that 
                            # the focus is on the filename? Might not be a bad idea from an 
                            # informational standpoint.
                            item, #filename
                            format_revision(rev.revision.key),
                            rev.revision.author_name,
                            format_date(rev.revision_date),
                            # *vals,
                            value,
                        )
                    )
    # before moving towards the print tabular data - the values are sorted according to the metric type
    # The "value" is assumed to be the fourth item in an individual data row. An alternative that may
    # be more readable is the op.attrgetter.
    if metric_meta["wily_metric_type"] == 'AimHigh':
        # AimHigh is sorted lowest to highest
        data.sort(key=op.itemgetter(4))
    elif metric_meta["wily_metric_type"] == 'AimLow':
        # AimLow is sorted highest to lowest
        data.sort(key=op.itemgetter(4), reverse=True)
    # TODO: Do we want to ignore informational types? Or we could sort them qualitatively (e.g., A>B)

    # Tack on the total row at the end
    data.append(aggregate_metric(data))

    headers = ("File", "Revision", "Author", "Date", metric_meta["title"])
    print(
        tabulate.tabulate(
            headers=headers,
            tabular_data=data,
            tablefmt=DEFAULT_GRID_STYLE
        )
    )


    def aggregate_metric(metric_table: list):
        """
            This function aggregates/totals wily metrics that in a tabular format.
            Data is assumed to be in the tabular format of the rank function within the rank.py
            command. 

            :param metric_table: table with list of wily metrics across multiple files.
            :type metric_table: ''list''

            :return: Sorted table of all files in path, sorted in order of metric.
        """
        # value in first draft is assumed to be the fifth item in the list.
        return ['Total','---', '---', '---', sum(metric_table[4])]

