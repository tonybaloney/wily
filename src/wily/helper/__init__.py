"""Helper package for wily."""
import sys

from wily.config import DEFAULT_GRID_STYLE


def get_style():
    """Select the tablefmt style for tabulate according to what sys.stdout can handle."""
    style = DEFAULT_GRID_STYLE
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        style = "grid"
    return style
