"""
Index command.

Print information about the wily cache and what is in the index.
"""

import sys
from pathlib import Path

from wily import MAX_MESSAGE_WIDTH, format_date, format_revision, logger
from wily.backend import WilyIndex
from wily.cache import get_default_metrics_path, list_archivers
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table


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
    logger.debug("Running index command")
    logger.info("--------Configuration---------")
    logger.info("Path: %s", config.path)
    logger.info("Archiver: %s", config.archiver)
    logger.info("Operators: %s", config.operators)
    logger.info("")
    logger.info("-----------History------------")

    archivers = list_archivers(config)
    if not archivers:
        logger.error("No wily cache found. Run 'wily build' first.")
        sys.exit(1)

    data: list[tuple[str, ...]] = []
    for archiver in archivers:
        parquet_path = get_default_metrics_path(config, archiver)
        if not Path(parquet_path).exists():
            continue

        # Get unique revisions from parquet
        with WilyIndex(parquet_path, []) as idx:
            # Collect unique revisions (keyed by revision hash)
            revisions: dict[str, dict] = {}
            for row in idx:
                rev_key = row["revision"]
                if rev_key not in revisions:
                    revisions[rev_key] = {
                        "key": rev_key,
                        "author": row.get("revision_author", "Unknown"),
                        "message": row.get("revision_message", ""),
                        "date": row.get("revision_date", 0),
                    }

            # Sort by date descending (most recent first)
            sorted_revisions = sorted(revisions.values(), key=lambda r: r["date"], reverse=True)

            for rev in sorted_revisions:
                if include_message:
                    message = rev["message"] or ""
                    data.append(
                        (
                            format_revision(rev["key"]),
                            str(rev["author"]),
                            message[:MAX_MESSAGE_WIDTH],
                            format_date(rev["date"]),
                        )
                    )
                else:
                    data.append(
                        (
                            format_revision(rev["key"]),
                            str(rev["author"]),
                            format_date(rev["date"]),
                        )
                    )

    headers: tuple[str, ...]
    if include_message:
        headers = ("Revision", "Author", "Message", "Date")
    else:
        headers = ("Revision", "Author", "Date")

    print_table(headers=headers, data=data, wrap=wrap, table_style=table_style)
