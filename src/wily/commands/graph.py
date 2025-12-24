"""
Graph command.

Draw graph in HTML for a specific metric.
"""

import sys
from pathlib import Path

import plotly.graph_objs as go
import plotly.offline

from wily import format_datetime, logger
from wily.backend import WilyIndex
from wily.cache import get_default_metrics_path
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_ARCHIVER
from wily.operators import Metric, resolve_metric, resolve_metric_as_tuple


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
    path: tuple[str, ...],
    metrics: str,
    output: str | None = None,
    x_axis: str | None = None,
    changes: bool = True,
    text: bool = False,
    aggregate: bool = False,
    plotlyjs: bool | str = True,
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
    archiver = config.archiver or DEFAULT_ARCHIVER

    # Get path to parquet index
    parquet_path = get_default_metrics_path(config, archiver)
    if not Path(parquet_path).exists():
        logger.error("Wily cache not found. Run 'wily build' first.")
        sys.exit(1)

    if x_axis is None:
        x_axis = "history"
        x_operator = x_key = ""
    else:
        x_operator, x_key = metric_parts(x_axis)

    metrics_list = metrics.split(",")

    y_metric = resolve_metric(metrics_list[0])
    operator, key = metric_parts(metrics_list[0])

    z_axis: Metric | str
    if len(metrics_list) == 1:  # only y-axis
        z_axis = z_operator = z_key = ""
    else:
        z_axis = resolve_metric(metrics_list[1])
        z_operator, z_key = metric_parts(metrics_list[1])

    # Initialize title with a default - will be updated once we know paths
    title = f"{x_axis.capitalize()} of {y_metric.description}"

    with WilyIndex(parquet_path, [operator]) as index:
        # Get all rows and organize by revision
        all_rows = list(index)
        if not all_rows:
            logger.error("No data in cache. Run 'wily build' first.")
            sys.exit(1)

        # Get unique revisions sorted by date (oldest first for graph)
        revisions: dict[str, dict] = {}
        for row in all_rows:
            rev_key = row["revision"]
            if rev_key not in revisions:
                revisions[rev_key] = {
                    "key": rev_key,
                    "author": row.get("revision_author", "Unknown"),
                    "message": row.get("revision_message", ""),
                    "date": row.get("revision_date", 0),
                }
        sorted_revisions = sorted(revisions.values(), key=lambda r: r["date"])
        revision_keys = [r["key"] for r in sorted_revisions]

        # Build lookup: {revision: {path: row_data}}
        revision_data: dict[str, dict[str, dict]] = {}
        tracked_files: set[str] = set()
        for row in all_rows:
            rev_key = row["revision"]
            file_path = row["path"]
            if rev_key not in revision_data:
                revision_data[rev_key] = {}
            revision_data[rev_key][file_path] = row
            tracked_files.add(file_path)

        if not aggregate:
            paths = tuple(
                tracked_file
                for tracked_file in tracked_files
                if any(path_startswith(tracked_file, p) or tracked_file.startswith(p) for p in path)
            ) or path
        else:
            paths = path

        title = f"{x_axis.capitalize()} of {y_metric.description}{(' for ' + paths[0]) if len(paths) == 1 else ''}{' aggregated' if aggregate else ''}"

        for path_ in paths:
            current_path = str(Path(path_))
            x = []
            y = []
            z = []
            labels = []
            last_y = None

            for rev in sorted_revisions:
                rev_key = rev["key"]
                rev_paths = revision_data.get(rev_key, {})

                # Try exact match or path starting with current_path
                row = rev_paths.get(current_path)
                if row is None:
                    # Try matching path that starts with current_path (for directories)
                    for p, r in rev_paths.items():
                        if p.startswith(current_path) or current_path.startswith(p):
                            row = r
                            break

                if row is None:
                    continue

                try:
                    val = row.get(key)
                    if val is None:
                        continue

                    if val != last_y or not changes:
                        y.append(val)
                        if z_axis:
                            z_val = row.get(z_key)
                            z.append(z_val if z_val is not None else 0)
                        if x_axis == "history":
                            x.append(format_datetime(rev["date"]))
                        else:
                            x_val = row.get(x_key)
                            x.append(x_val if x_val is not None else 0)
                        labels.append(f"{rev['author']} <br>{rev['message']}")
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
                ids=revision_keys,
                text=labels,
                marker={
                    "size": 0 if not z_axis else z,
                    "color": list(range(len(y))),
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

