from wily import logger, format_date
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType

import plotly.offline
import plotly.plotly as py
import plotly.graph_objs as go



def graph(config, path, metric):
    """
    Graph information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param path: The path to the file
    :type  path: ``str``

    :param metric: The metric to report on
    :type  metric: The metric

    :return:
    """
    logger.debug("Running report command")

    i = 0
    x = []
    y = []
    operator, key = metric.split('.')
    metric = resolve_metric(metric)
    archivers = cache.list_archivers()

    for archiver in archivers:
        # We have to do it backwards to get the deltas between releases
        history = cache.get_index(archiver)
        ids = [rev['revision'] for rev in history[::-1]]
        labels = [f"{rev['author_name']} <br>{rev['message']}" for rev in history[::-1]]
        for rev in history[::-1]:
            revision_entry = cache.get(archiver, rev['revision'])
            try:
                val = revision_entry["operator_data"][operator][path][key]
                y.append(val)
            except KeyError:
                y.append(0)
            finally:
                x.append(i)
                i+=1
    # Create traces
    trace0 = go.Scatter(
        x = x,
        y = y,
        mode = 'lines+markers',
        name = metric[1],
        ids = ids,
        text = labels
    )
    data = [trace0]
    plotly.offline.plot(
        {"data": data, 
        "layout": go.Layout(title=f"History of {metric[1]}")}
        , auto_open=True)
