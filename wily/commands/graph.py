from wily import logger, format_date
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType

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
        for rev in history:
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
        name = metric[1]
    )
    data = [trace0]
    py.iplot(data, filename='line-mode')
