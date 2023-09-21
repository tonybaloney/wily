"""Helper package for wily."""
import hashlib
import logging
import pathlib
import shutil
import sys
from functools import lru_cache
from typing import Optional, Sized, Union

from wily.defaults import DEFAULT_GRID_STYLE

logger = logging.getLogger(__name__)


def get_maxcolwidth(headers: Sized, wrap=True) -> Optional[int]:
    """Calculate the maximum column width for a given terminal width."""
    if not wrap:
        return None
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


def get_style(style: str = DEFAULT_GRID_STYLE) -> str:
    """Select the tablefmt style for tabulate according to what sys.stdout can handle."""
    if style == DEFAULT_GRID_STYLE:
        encoding = sys.stdout.encoding
        # StringIO has encoding=None, but it handles utf-8 fine.
        if encoding is not None and encoding.lower() not in ("utf-8", "utf8"):
            style = "grid"
    return style


@lru_cache(maxsize=128)
def generate_cache_path(path: Union[pathlib.Path, str]) -> str:
    """
    Generate a reusable path to cache results.

    Will use the --path of the target and hash into
    a 9-character directory within the HOME folder.

    :return: The cache path
    """
    logger.debug("Generating cache for %s", path)
    sha = hashlib.sha1(str(path).encode()).hexdigest()[:9]
    HOME = pathlib.Path.home()
    cache_path = str(HOME / ".wily" / sha)
    logger.debug("Cache path is %s", cache_path)
    return cache_path
