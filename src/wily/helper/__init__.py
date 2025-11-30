"""Helper package for wily."""

import hashlib
import logging
import pathlib
from collections.abc import Iterable
from functools import lru_cache

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from wily.defaults import DEFAULT_TABLE_STYLE

logger = logging.getLogger(__name__)

# Map of style names to Rich box objects
BOX_STYLES = {
    "ASCII": box.ASCII,
    "ASCII2": box.ASCII2,
    "ASCII_DOUBLE_HEAD": box.ASCII_DOUBLE_HEAD,
    "SQUARE": box.SQUARE,
    "SQUARE_DOUBLE_HEAD": box.SQUARE_DOUBLE_HEAD,
    "MINIMAL": box.MINIMAL,
    "MINIMAL_HEAVY_HEAD": box.MINIMAL_HEAVY_HEAD,
    "MINIMAL_DOUBLE_HEAD": box.MINIMAL_DOUBLE_HEAD,
    "SIMPLE": box.SIMPLE,
    "SIMPLE_HEAD": box.SIMPLE_HEAD,
    "SIMPLE_HEAVY": box.SIMPLE_HEAVY,
    "HORIZONTALS": box.HORIZONTALS,
    "ROUNDED": box.ROUNDED,
    "HEAVY": box.HEAVY,
    "HEAVY_EDGE": box.HEAVY_EDGE,
    "HEAVY_HEAD": box.HEAVY_HEAD,
    "DOUBLE": box.DOUBLE,
    "DOUBLE_EDGE": box.DOUBLE_EDGE,
    "MARKDOWN": box.MARKDOWN,
}


def get_box_style(style: str = DEFAULT_TABLE_STYLE) -> box.Box:
    """
    Get a Rich box style by name.

    :param style: Name of the box style (case-insensitive)
    :return: A Rich Box object
    """
    return BOX_STYLES.get(style.upper(), box.ROUNDED)


def styled_text(text: str, style: str) -> Text:
    """
    Create a Rich Text object with the given style.

    :param text: The text content
    :param style: The Rich style name (e.g., 'red', 'green', 'yellow')
    :return: A Rich Text object
    """
    return Text(text, style=style)


def print_table(
    headers: Iterable[str],
    data: Iterable[Iterable[str | Text]],
    wrap: bool = True,
    table_style: str = DEFAULT_TABLE_STYLE,
) -> None:
    """
    Print a table using Rich.

    :param headers: Column headers
    :param data: Table data rows (can contain strings or Rich Text objects)
    :param wrap: Whether to wrap long content
    :param table_style: Box style name (e.g., 'ROUNDED', 'SIMPLE', 'ASCII')
    """
    console = Console()
    box_style = get_box_style(table_style)
    table = Table(show_header=True, header_style="bold", box=box_style)

    headers_list = list(headers)

    for header in headers_list:
        table.add_column(header, overflow="fold" if wrap else "ignore")

    for row in data:
        # Convert to strings if needed, but preserve Text objects
        processed_row = [cell if isinstance(cell, Text) else str(cell) for cell in row]
        table.add_row(*processed_row)

    console.print(table)


@lru_cache(maxsize=128)
def generate_cache_path(path: pathlib.Path | str) -> str:
    """
    Generate a reusable path to cache results.

    Will use the --path of the target and hash into
    a 9-character directory within the HOME folder.

    :return: The cache path
    """
    logger.debug("Generating cache for %s", path)
    sha = hashlib.sha1(str(path).encode()).hexdigest()[:9]  # noqa: S324
    HOME = pathlib.Path.home()
    cache_path = str(HOME / ".wily" / sha)
    logger.debug("Cache path is %s", cache_path)
    return cache_path
