"""
Draw graph in HTML for a specific metric.

TODO: Add multiple lines for multiple files
"""

from pathlib import Path

import plotly.graph_objs as go
import plotly.offline

from wily import format_datetime, logger
from wily.operators import resolve_metric, resolve_metric_as_tuple
from wily.state import State


def metric_parts(metric):
    """Convert a metric name into the operator and metric names."""
    operator, met = resolve_metric_as_tuple(metric)
    return operator.name, met.name


def graph(
    config,
    path,
    metrics,
    output=None,
    x_axis=None,
    changes=True,
    text=False,
    aggregate=False,
):
    """
    Graph information about the cache and runtime.

    :param config: The configuration.
    :type  config: :class:`wily.config.WilyConfig`

    :param path: The path to the files.
    :type  path: ``str``

    :param metrics: The Y and Z-axis metrics to report on.
    :type  metrics: ``tuple``

    :param output: Save report to specified path instead of opening browser.
    :type  output: ``str``

    :param x_axis: Name of metric for x-axis or "history".
    :type x_axis: ``str``

    :param changes: Only graph changes.
    :type changes: ``bool``

    :param text: Show commit message inline in graph.
    :type text: ``bool``

    :param aggregate: Aggregate values for graph.
    :type aggregate: ``bool``
    """
    logger.debug("Running graph command")

    data = []
    state = State(config)

    if x_axis is None:
        x_axis = "history"
    else:
        x_operator, x_key = metric_parts(x_axis)

    y_metric = resolve_metric(metrics[0])
    title = f"{x_axis.capitalize()} of {y_metric.description} for {path}{' aggregated' if aggregate else ''}"

    if not aggregate:
        tracked_files = set()
        for rev in state.index[state.default_archiver].revisions:
            tracked_files.update(rev.revision.tracked_files)
        paths = {
            tracked_file
            for tracked_file in tracked_files
            if tracked_file.startswith(path)
        } or {path}
    else:
        paths = {path}

    operator, key = metric_parts(metrics[0])
    if len(metrics) == 1:  # only y-axis
        z_axis = None
    else:
        z_axis = resolve_metric(metrics[1])
        z_operator, z_key = metric_parts(metrics[1])
    for path_ in paths:
        current_path = str(Path(path_))
        x = []
        y = []
        z = []
        labels = []
        last_y = None
        for rev in state.index[state.default_archiver].revisions:
            try:
                val = rev.get(
                    config, state.default_archiver, operator, current_path, key
                )
                if val != last_y or not changes:
                    y.append(val)
                    if z_axis:
                        z.append(
                            rev.get(
                                config,
                                state.default_archiver,
                                z_operator,
                                current_path,
                                z_key,
                            )
                        )
                    if x_axis == "history":
                        x.append(format_datetime(rev.revision.date))
                    else:
                        x.append(
                            rev.get(
                                config,
                                state.default_archiver,
                                x_operator,
                                current_path,
                                x_key,
                            )
                        )
                    labels.append(
                        f"{rev.revision.author_name} <br>{rev.revision.message}"
                    )
                last_y = val
            except KeyError:
                # missing data
                pass

        # Create traces
        trace = go.Scatter(
            x=x,
            y=y,
            mode="lines+markers+text" if text else "lines+markers",
            name=f"{path}",
            ids=state.index[state.default_archiver].revision_keys,
            text=labels,
            marker={
                "size": 0 if z_axis is None else z,
                "color": list(range(len(y))),
                # "colorscale": "Viridis",
            },
            xcalendar="gregorian",
            hoveron="points+fills",
        )
        data.append(trace)
    if output:
        filename = output
        auto_open = False
    else:
        filename = "wily-report.html"
        auto_open = True
    plotly.offline.plot(
        {
            "data": data,
            "layout": go.Layout(
                title=title,
                xaxis={"title": x_axis},
                yaxis={"title": y_metric.description},
            ),
        },
        auto_open=auto_open,
        filename=filename,
    )
