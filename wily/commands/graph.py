"""
Draw graph in HTML for a specific metric.

TODO: Add multiple lines for multiple files
"""
from wily import logger, format_datetime
from wily.operators import resolve_metric
from wily.state import State
import plotly.offline
import plotly.graph_objs as go
import pathlib


def graph(config, path, metrics, output=None):
    """
    Graph information about the cache and runtime.

    :param config: The configuration.
    :type  config: :class:`wily.config.WilyConfig`

    :param paths: The path(s) to the files.
    :type  paths: ``list``

    :param metrics: The metrics to report on.
    :type  metrics: ``tuple``

    :param output: Save report to specified path instead of opening browser.
    :type  output: ``str``
    """
    logger.debug("Running report command")

    data = []
    state = State(config)
    abs_path = config.path / pathlib.Path(path)

    if abs_path.is_dir():
        paths = [p.relative_to(config.path) for p in pathlib.Path(abs_path).glob('**/*.py')]
    else:
        paths = [path]

    for metric in metrics:
        operator, key = metric.split(".")
        metric = resolve_metric(metric)
        for path in paths:
            x = []
            y = []
            labels = []
            for archiver in state.archivers:
                # We have to do it backwards to get the deltas between releases
                for rev in state.index[archiver].revisions[::-1]:
                    labels.append(f"{rev.revision.author_name} <br>{rev.revision.message}")
                    try:
                        val = rev.get(config, archiver, operator, str(path), key)
                        y.append(val)
                    except KeyError:
                        y.append(0)
                    finally:
                        x.append(format_datetime(rev.revision.date))
            # Create traces
            trace = go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=f"{metric.description} for {path}",
                ids=state.index[archiver].revision_keys,
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
