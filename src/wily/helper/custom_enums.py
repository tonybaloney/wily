"""A module containing custom enums for wily."""
from enum import Enum


class ReportFormat(Enum):
    """Represent the available report formats."""

    CONSOLE = 1
    HTML = 2

    @classmethod
    def get_all(cls):
        """Return a list with all Enumerations."""
        return [format.name for format in cls]
