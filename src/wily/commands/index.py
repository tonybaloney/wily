"""
Index command.

Print information about the wily cache and what is in the index.
"""

from wily import MAX_MESSAGE_WIDTH, format_date, format_revision, logger
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.state import State


def index(
    config: WilyConfig,
    include_message: bool = False,
    wrap: bool = False,
    table_style: str = DEFAULT_TABLE_STYLE,
) -> None:
    """
    Show information about the cache and runtime.

    :param config: The wily configuration
    :param include_message: Include revision messages
    :param wrap: Wrap long lines
    :param table_style: Table box style
    """
    state = State(config=config)
    logger.debug("Running show command")
    logger.info("--------Configuration---------")
    logger.info("Path: %s", config.path)
    logger.info("Archiver: %s", config.archiver)
    logger.info("Operators: %s", config.operators)
    logger.info("")
    logger.info("-----------History------------")

    data: list[tuple[str, ...]] = []
    for archiver in state.archivers:
        for rev in state.index[archiver].revisions:
            if include_message:
                data.append(
                    (
                        format_revision(rev.revision.key),
                        str(rev.revision.author_name),
                        rev.revision.message[:MAX_MESSAGE_WIDTH],
                        format_date(rev.revision.date),
                    )
                )
            else:
                data.append(
                    (
                        format_revision(rev.revision.key),
                        str(rev.revision.author_name),
                        format_date(rev.revision.date),
                    )
                )

    headers: tuple[str, ...]
    if include_message:
        headers = ("Revision", "Author", "Message", "Date")
    else:
        headers = ("Revision", "Author", "Date")

    print_table(headers=headers, data=data, wrap=wrap, table_style=table_style)
