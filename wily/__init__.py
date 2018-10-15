"""
A Python application for tracking, reporting on timing and complexity in tests and applications.
"""
import colorlog
import datetime


__version__ = "0.5.0"

_handler = colorlog.StreamHandler()
_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))

logger = colorlog.getLogger(__name__)
logger.addHandler(_handler)


def format_date(timestamp):
    """ Reusable timestamp -> date """
    return datetime.date.fromtimestamp(timestamp).isoformat()
