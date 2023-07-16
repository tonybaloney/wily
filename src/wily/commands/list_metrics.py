"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""
import tabulate

from wily.config import DEFAULT_GRID_STYLE
from wily.helper import get_maxcolwidth
from wily.operators import ALL_OPERATORS


def list_metrics(wrap):
    """List metrics available."""
    headers = ("Name", "Description", "Type", "Measure", "Aggregate")
    maxcolwidth = get_maxcolwidth(headers, wrap)
    for name, operator in ALL_OPERATORS.items():
        print(f"{name} operator:")
        if len(operator.cls.metrics) > 0:
            print(
                tabulate.tabulate(
                    headers=headers,
                    tabular_data=operator.cls.metrics,
                    tablefmt=DEFAULT_GRID_STYLE,
                    maxcolwidths=maxcolwidth,
                    maxheadercolwidths=maxcolwidth,
                )
            )
