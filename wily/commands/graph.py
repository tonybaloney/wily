"""
Draw graph in HTML for a specific metric

TODO: Add multiple lines for multiple files
"""
from wily import logger, format_datetime, format_revision
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType, get_metric

import plotly.offline
import plotly.plotly as py
import plotly.graph_objs as go


def graph(config, paths, metrics, output=None):
    """
    Graph information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param paths: The path(s) to the files
    :type  paths: ``list``

    :param metrics: The metrics to report on
    :type  metrics: ``tuple``

    :param output: Save report to specified path instead of opening browser
    :type  output: ``str``
    """
    logger.debug("Running report command")

    data = []

    archivers = cache.list_archivers(config)

    for metric in metrics:
        operator, key = metric.split(".")
        metric = resolve_metric(metric)
        for path in paths:
            x = []
            y = []
            for archiver in archivers:
                # We have to do it backwards to get the deltas between releases
                history = cache.get_index(config, archiver)
                ids = [rev["revision"] for rev in history[::-1]]
                labels = [
                    f"{rev['author_name']} <br>{rev['message']}"
                    for rev in history[::-1]
                ]
                for rev in history[::-1]:
                    revision_entry = cache.get(config, archiver, rev["revision"])
                    try:
                        val = get_metric(
                            revision_entry["operator_data"], operator, path, key
                        )
                        y.append(val)
                    except KeyError:
                        y.append(0)
                    finally:
                        x.append(format_datetime(rev["date"]))
            # Create traces
            trace = go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=f"{metric.description} for {path}",
                ids=ids,
                text=labels,
                xcalendar="gregorian",
            )
            data.append(trace)
    if output:
        filename = output
        auto_open = False
    else:
        filename = "wily-report.html"
        auto_open = True
    if len(metrics) == 1:
        metric = resolve_metric(metrics[0])
        title = f"History of {metric.description}"
    else:
        descriptions = ", ".join(
            [resolve_metric(metric).description for metric in metrics]
        )
        title = f"History of {descriptions}"
    plotly.offline.plot(
        {"data": data, "layout": go.Layout(title=title)},
        auto_open=auto_open,
        filename=filename,
    )
