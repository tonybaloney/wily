"""Helper package for wily."""
import shutil


def get_maxcolwidth(headers, wrap=True):
    """Calculate the maximum column width for a given terminal width."""
    if not wrap:
        return
    width = shutil.get_terminal_size()[0]
    columns = len(headers)
    if width > 125:
        padding = 2
    elif width > 95:
        padding = 3
    else:
        padding = 5
    maxcolwidth = width // columns - padding - 1
    if not width % columns:
        maxcolwidth -= 2
    return max(maxcolwidth, 1)
