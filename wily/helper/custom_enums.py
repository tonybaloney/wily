from enum import Enum


class ReportFormat(Enum):
    CONSOLE = 1
    HTML = 2

    @classmethod
    def get_all(cls):
        """Returns a list with all Enumerations"""
        return [format.name for format in cls]
