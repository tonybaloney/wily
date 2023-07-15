"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""
import sys

import tabulate

from wily.config import DEFAULT_GRID_STYLE
from wily.operators import ALL_OPERATORS


def list_metrics():
    """List metrics available."""
    style = DEFAULT_GRID_STYLE
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        style = "grid"
    for name, operator in ALL_OPERATORS.items():
        print(f"{name} operator:")
        if len(operator.cls.metrics) > 0:
            print(
                tabulate.tabulate(
                    headers=("Name", "Description", "Type"),
                    tabular_data=operator.cls.metrics,
                    tablefmt=style,
                )
            )
