"""Helper package for wily."""
import shutil


def get_maxcolwidth(headers, wrap=True):
    """Calculate the maximum column width for a given terminal width."""
    if not wrap:
        return
    width = shutil.get_terminal_size()[0]
    columns = len(headers)
    if width < 80:
        padding = columns + 1
    elif width < 120:
        padding = columns - 2
    else:
        padding = columns - 4
    maxcolwidth = (width // columns) - padding
    return max(maxcolwidth, 1)
