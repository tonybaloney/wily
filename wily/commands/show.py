from wily import logger
import tabulate
from wily.cache import list_archivers, get_history


def show(config):
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
    archivers = list_archivers()
    for archiver in archivers:
        history = get_history(archiver)
        for rev in history:
            data.append(
                (
                    rev["revision"],
                    rev["author_name"],
                    ", ".join(list(rev["operator_data"].keys())),
                )
            )

    logger.info(
        tabulate.tabulate(
            headers=("Revision", "Author", "Operators"), tabular_data=data
        )
    )
