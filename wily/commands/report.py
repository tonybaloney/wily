from wily import logger
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
from wily.cache import list_archivers, get_history


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
    archivers = list_archivers()
    for archiver in archivers:
        history = get_history(archiver)
        for rev in history:
            try:
                val = rev["operator_data"][operator][path][key]
                if last:
                    delta=val-last
                    last=val
                else:
                    delta=0
                if delta == 0:
                    delta_col = delta
                elif delta < 0 :
                    delta_col = f"\u001b[32m-{delta}\u001b[0m"
                else:
                    delta_col = f"\u001b[31m+{delta}\u001b[0m"
                data.append(
                    (
                        rev["revision"],
                        rev["author_name"],
                        f"{val} ({delta_col})",
                    )
                )
            except KeyError:
                data.append(
                    (
                        rev["revision"],
                        rev["author_name"],
                        "Not found",
                    )
                )

    print(
        tabulate.tabulate(
            headers=("Revision", "Author", metric), tabular_data=data,
            tablefmt=DEFAULT_GRID_STYLE
        )
    )
