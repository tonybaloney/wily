from wily import logger, format_date
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType


def report(config, path, metric):
    """
    Show information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param path: The path to the file
    :type  path: ``str``

    :param metric: The metric to report on
    :type  metric: The metric

    :return:
    """
    logger.debug("Running report command")

    logger.info(f"-----------History for {metric}------------")

    data = []
    last = None
    operator, key = metric.split('.')
    metric = resolve_metric(metric)
    archivers = cache.list_archivers()

    # Set the delta colors depending on the metric type
    if metric[3] == MetricType.AimHigh:
        good_color = 32
        bad_color = 31
    elif metric[3] == MetricType.AimLow:
        good_color = 31
        bad_color = 32
    elif metric[3] == MetricType.Informational:
        good_color = 33
        bad_color = 33 

    for archiver in archivers:
        # We have to do it backwards to get the deltas between releases
        history = cache.get_index(archiver)[::-1]
        for rev in history:
            revision_entry = cache.get(archiver, rev['revision'])
            try:
                val = revision_entry["operator_data"][operator][path][key]

                # Measure the difference between this value and the last
                if last:
                    delta=val-last
                else:
                    delta=0
                last=val

                # TODO : Format floating values nicely
                if delta == 0:
                    delta_col = delta
                elif delta < 0 :
                    delta_col = f"\u001b[{good_color}m{delta}\u001b[0m"
                else:
                    delta_col = f"\u001b[{bad_color}m+{delta}\u001b[0m"

                data.append(
                    (
                        rev["revision"],
                        rev["author_name"],
                        format_date(rev["date"]),
                        f"{val} ({delta_col})",
                    )
                )
            except KeyError:
                data.append(
                    (
                        rev["revision"],
                        rev["author_name"],
                        format_date(rev["date"]),
                        "Not found",
                    )
                )

    print(
        # But it still makes more sense to show the newest at the top, so reverse again
        tabulate.tabulate(
            headers=("Revision", "Author", "Date", metric[1]), tabular_data=data[::-1],
            tablefmt=DEFAULT_GRID_STYLE
        )
    )
