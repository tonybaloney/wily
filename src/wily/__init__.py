"""
Wily.

A Python application for tracking, reporting on timing and complexity in tests and applications.
"""
import tempfile
import colorlog
import logging
import datetime

WILY_LOG_NAME = tempfile.mkstemp(suffix="wily_log")

__version__ = "1.17.0"

_handler = colorlog.StreamHandler()
_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))

_filehandler = logging.FileHandler(WILY_LOG_NAME, mode="w+")
_filehandler.setLevel(logging.DEBUG)

logger = colorlog.getLogger(__name__)
logger.addHandler(_handler)
logger.addHandler(_filehandler)

""" Max number of characters of the Git commit to print """
MAX_MESSAGE_WIDTH = 50


def format_date(timestamp):
    """Reusable timestamp -> date."""
    return datetime.date.fromtimestamp(timestamp).isoformat()


def format_datetime(timestamp):
    """Reusable timestamp -> datetime."""
    return datetime.datetime.fromtimestamp(timestamp).isoformat()


def format_revision(sha):
    """Return a shorter git sha."""
    return sha[:7]
