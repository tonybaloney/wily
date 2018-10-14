from wily import logger
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH
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
    operator, key = metric.split('.')
    archivers = list_archivers()
    for archiver in archivers:
        history = get_history(archiver)
        for rev in history:
            try:
                data.append(
                    (
                        rev["revision"],
                        rev["author_name"],
                        rev["operator_data"][operator][path][key],
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

    logger.info(
        tabulate.tabulate(
            headers=("Revision", "Author", metric), tabular_data=data,

        )
    )
