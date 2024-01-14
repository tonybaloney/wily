"""Helper package for wily."""
import hashlib
import logging
import pathlib
import shutil
import sys
from functools import lru_cache
from typing import Optional, Sized, Union

import tabulate

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


strip_ansi = tabulate._strip_ansi  # type: ignore
ansi_codes = tabulate._ansi_codes  # type: ignore


def handle_long_word(
    self, reversed_chunks: list[str], cur_line: list[str], cur_len: int, width: int
):
    """
    Handle a chunk of text that is too long to fit in any line.

    Fixed version of tabulate._CustomTextWrap._handle_long_word that avoids a
    wrapping bug (https://github.com/astanin/python-tabulate/issues/307) where
    ANSI escape codes would be broken up in the middle.
    """
    # Figure out when indent is larger than the specified width, and make
    # sure at least one character is stripped off on every pass
    if width < 1:
        space_left = 1
    else:
        space_left = width - cur_len

    # If we're allowed to break long words, then do so: put as much
    # of the next chunk onto the current line as will fit.
    if self.break_long_words:
        # Tabulate Custom: Build the string up piece-by-piece in order to
        # take each character's width into account
        chunk = reversed_chunks[-1]
        i = 1
        # Only count printable characters, so strip_ansi first, index later.
        while len(strip_ansi(chunk)[:i]) <= space_left:
            i = i + 1
        # Consider escape codes when breaking words up
        total_escape_len = 0
        last_group = 0
        if ansi_codes.search(chunk) is not None:
            for group, _, _, _ in ansi_codes.findall(chunk):
                escape_len = len(group)
                if group in chunk[last_group : i + total_escape_len + escape_len - 1]:
                    total_escape_len += escape_len
                    found = ansi_codes.search(chunk[last_group:])
                    last_group += found.end()
        cur_line.append(chunk[: i + total_escape_len - 1])
        reversed_chunks[-1] = chunk[i + total_escape_len - 1 :]

    # Otherwise, we have to preserve the long word intact.  Only add
    # it to the current line if there's nothing already there --
    # that minimizes how much we violate the width constraint.
    elif not cur_line:
        cur_line.append(reversed_chunks.pop())

    # If we're not allowed to break long words, and there's already
    # text on the current line, do nothing.  Next time through the
    # main loop of _wrap_chunks(), we'll wind up here again, but
    # cur_len will be zero, so the next line will be entirely
    # devoted to the long word that we can't handle right now.
