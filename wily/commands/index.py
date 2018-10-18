"""
Print information about the wily cache and what is in the index

TODO : Optional flag to include commit messages in table

"""
from wily import logger, format_date, format_revision
import tabulate
import wily.cache as cache
from wily.config import DEFAULT_GRID_STYLE


def index(config):
    """
    Show information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :return:
    """
    logger.debug("Running show command")
    logger.info("--------Configuration---------")
    logger.info(f"Path: {config.path}")
    logger.info(f"Archiver: {config.archiver}")
    logger.info(f"Operators: {config.operators}")
    logger.info("")
    logger.info("-----------History------------")

    data = []
    archivers = cache.list_archivers()
    for archiver in archivers:
        history = cache.get_index(archiver)
        for rev in history:
            data.append(
                (
                    format_revision(rev["revision"]),
                    rev["author_name"],
                    format_date(rev["date"]),
                )
            )

    print(
        tabulate.tabulate(
            headers=("Revision", "Author", "Date"), tabular_data=data,
            tablefmt=DEFAULT_GRID_STYLE
        )
    )
