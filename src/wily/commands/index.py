"""
Print command.

Print information about the wily cache and what is in the index.
"""
from typing import List, Tuple, Sequence

import tabulate

from wily import logger, format_date, format_revision, MAX_MESSAGE_WIDTH
from wily.config import DEFAULT_GRID_STYLE, WilyConfig
from wily.state import State


def index(config: WilyConfig, include_message: bool = False):
    """
    Show information about the cache and runtime.

    :param config: The wily configuration
    :param include_message: Include revision messages
    """
    state = State(config=config)
    logger.debug("Running show command")
    logger.info("--------Configuration---------")
    logger.info(f"Path: {config.path}")
    logger.info(f"Archiver: {config.archiver}")
    logger.info(f"Operators: {config.operators}")
    logger.info("")
    logger.info("-----------History------------")

    data: List[Tuple[str, ...]] = []
    for archiver in state.archivers:
        for rev in state.get_index(archiver).revisions:
            if include_message:
                data.append(
                    (
                        format_revision(rev.revision.key),
                        rev.revision.author_name,
                        rev.revision.message[:MAX_MESSAGE_WIDTH],
                        format_date(rev.revision.date),
                    )
                )
            else:
                data.append(
                    (
                        format_revision(rev.revision.key),
                        rev.revision.author_name,
                        format_date(rev.revision.date),
                    )
                )
    headers: Sequence[str] = ("Revision", "Author", "Message", "Date") if include_message else ("Revision", "Author", "Date")
    print(
        tabulate.tabulate(
            headers=headers, tabular_data=data, tablefmt=DEFAULT_GRID_STYLE
        )
    )
