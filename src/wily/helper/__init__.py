"""Helper package for wily."""
import shutil
import sys

from wily.config import DEFAULT_GRID_STYLE


def get_maxcolwidth(headers, wrap=True):
    """Calculate the maximum column width for a given terminal width."""
    if not wrap:
        return
    width = shutil.get_terminal_size()[0]
    columns = len(headers)
    if width < 80:
        padding = columns + 2
    elif width < 120:
        padding = columns - 2
    else:
        padding = columns - 4
    maxcolwidth = (width // columns) - padding
    return max(maxcolwidth, 1)


def get_style(style=DEFAULT_GRID_STYLE):
    """Select the tablefmt style for tabulate according to what sys.stdout can handle."""
    if style == DEFAULT_GRID_STYLE:
        encoding = sys.stdout.encoding
        # StringIO has encoding=None, but it handles utf-8 fine.
        if encoding is not None and encoding.lower() not in ("utf-8", "utf8"):
            style = "grid"
    return style
