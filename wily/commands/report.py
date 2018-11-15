"""
The report command gives a table of metrics for a specified list of files.
Will compare the values between revisions and highlight changes in green/red.
"""
from wily import logger, format_date, format_revision, MAX_MESSAGE_WIDTH
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType, get_metric


def report(config, path, metrics, n, include_message=False):
    """
    Show information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param path: The path to the file
    :type  path: ``str``

    :param metrics: Name of the metric to report on
    :type  metrics: ``str``

    :param n: Number of items to list
    :type  n: ``int``
    """
    logger.debug("Running report command")

    logger.info(f"-----------History for {metrics}------------")

    data = []
    last = None
    archivers = cache.list_archivers(config)

    metric_metas = []
    for metric in metrics:
        operator, key = metric.split(".")
        metric = resolve_metric(metric)
        # Set the delta colors depending on the metric type
        if metric.measure == MetricType.AimHigh:
            good_color = 32
            bad_color = 31
        elif metric.measure == MetricType.AimLow:
            good_color = 31
            bad_color = 32
        elif metric.measure == MetricType.Informational:
            good_color = 33
            bad_color = 33
        metric_meta = {
            "key": key,
            "operator": operator,
            "good_color": good_color,
            "bad_color": bad_color,
            "title": metric.description,
            "type": metric.type,
        }
        metric_metas.append(metric_meta)

    for archiver in archivers:
        history = cache.get_index(config, archiver)[:n]
        # We have to do it backwards to get the deltas between releases
        history = history[::-1]
        last = {}
        for rev in history:
            revision_entry = cache.get(config, archiver, rev["revision"])
            vals = []
            for meta in metric_metas:
                try:
                    logger.debug(
                        f"Fetching metric {meta['key']} for {meta['operator']} in {path}"
                    )
                    val = get_metric(
                        revision_entry["operator_data"],
                        meta["operator"],
                        path,
                        meta["key"],
                    )

                    last_val = last.get(meta["key"], None)
                    # Measure the difference between this value and the last
                    if meta["type"] in (int, float):
                        if last_val:
                            delta = val - last_val
                        else:
                            delta = 0
                        last[meta["key"]] = val
                    else:
                        # TODO : Measure ranking increases/decreases for str types?
                        delta = 0

                    if delta == 0:
                        delta_col = delta
                    elif delta < 0:
                        delta_col = f"\u001b[{meta['good_color']}m{delta:n}\u001b[0m"
                    else:
                        delta_col = f"\u001b[{meta['bad_color']}m+{delta:n}\u001b[0m"

                    if meta["type"] in (int, float):
                        k = f"{val:n} ({delta_col})"
                    else:
                        k = f"{val}"
                except KeyError:
                    k = "Not found"
                vals.append(k)
            if include_message:
                data.append(
                    (
                        format_revision(rev["revision"]),
                        rev["message"][:MAX_MESSAGE_WIDTH],
                        rev["author_name"],
                        format_date(rev["date"]),
                        *vals,
                    )
                )
            else:
                data.append(
                    (
                        format_revision(rev["revision"]),
                        rev["author_name"],
                        format_date(rev["date"]),
                        *vals,
                    )
                )
    descriptions = [meta["title"] for meta in metric_metas]
    if include_message:
        headers = ("Revision", "Message", "Author", "Date", *descriptions)
    else:
        headers = ("Revision", "Author", "Date", *descriptions)
    print(
        # But it still makes more sense to show the newest at the top, so reverse again
        tabulate.tabulate(
            headers=headers, tabular_data=data[::-1], tablefmt=DEFAULT_GRID_STYLE
        )
    )
