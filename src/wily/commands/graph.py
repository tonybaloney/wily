"""
Graph command.

Draw graph in HTML for a specific metric.
"""

from pathlib import Path
from typing import Optional, Tuple, Union

import plotly.graph_objs as go
import plotly.offline

from wily import format_datetime, logger
from wily.config.types import WilyConfig
from wily.operators import Metric, resolve_metric, resolve_metric_as_tuple
from wily.state import State


def metric_parts(metric):
    """Convert a metric name into the operator and metric names."""
    operator, met = resolve_metric_as_tuple(metric)
    return operator.name, met.name


def path_startswith(filename: str, path: str) -> bool:
    """Check whether a filename starts with a given path in platform-agnostic way."""
    filepath = Path(filename).resolve()
    path_ = Path(path).resolve()
    return str(filepath).startswith(str(path_))


def graph(
    config: WilyConfig,
    path: Tuple[str, ...],
    metrics: str,
    output: Optional[str] = None,
    x_axis: Optional[str] = None,
    changes: bool = True,
    text: bool = False,
    aggregate: bool = False,
    plotlyjs: Union[bool, str] = True,
) -> None:
    """
    Graph information about the cache and runtime.

    :param config: The configuration.
    :param path: The path to the files.
    :param metrics: The Y and Z-axis metrics to report on.
    :param output: Save report to specified path instead of opening browser.
    :param x_axis: Name of metric for x-axis or "history".
    :param changes: Only graph changes.
    :param text: Show commit message inline in graph.
    :param aggregate: Aggregate values for graph.
    :param plotlyjs: How to include plotly.min.js.
    """
    logger.debug("Running graph command")

    data = []
    state = State(config)

    if x_axis is None:
        x_axis = "history"
        x_operator = x_key = ""
    else:
        x_operator, x_key = metric_parts(x_axis)

    metrics_list = metrics.split(",")

    y_metric = resolve_metric(metrics_list[0])

    if not aggregate:
        tracked_files = set()
        for rev in state.index[state.default_archiver].revisions:
            tracked_files.update(rev.revision.tracked_files)
        paths = (
            tuple(
                tracked_file
                for tracked_file in tracked_files
                if any(path_startswith(tracked_file, p) for p in path)
            )
            or path
        )
    else:
        paths = path

    title = (
        f"{x_axis.capitalize()} of {y_metric.description}"
        f"{(' for ' + paths[0]) if len(paths) == 1 else ''}{' aggregated' if aggregate else ''}"
    )
    operator, key = metric_parts(metrics_list[0])
    z_axis: Union[Metric, str]
    if len(metrics_list) == 1:  # only y-axis
        z_axis = z_operator = z_key = ""
    else:
        z_axis = resolve_metric(metrics_list[1])
        z_operator, z_key = metric_parts(metrics_list[1])
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
            name=f"{path_}",
            ids=state.index[state.default_archiver].revision_keys,
            text=labels,
            marker={
                "size": 0 if not z_axis else z,
                "color": list(range(len(y))),
                # "colorscale": "Viridis",
            },
            xcalendar="gregorian",
            hoveron="points+fills",
        )  # type: ignore
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
            ),  # type: ignore
        },
        auto_open=auto_open,
        filename=filename,
        include_plotlyjs=plotlyjs,  # type: ignore
    )
