"""
Wily.

A Python application for tracking, reporting on timing and complexity in tests and applications.
"""
import colorlog
import datetime


__version__ = "1.8.1"

_handler = colorlog.StreamHandler()
_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))

logger = colorlog.getLogger(__name__)
logger.addHandler(_handler)

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
