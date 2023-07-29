"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""
import tabulate

from wily.helper import get_maxcolwidth, get_style
from wily.operators import ALL_OPERATORS


def list_metrics(wrap):
    """List metrics available."""
    headers = ("Name", "Description", "Type", "Measure", "Aggregate")
    maxcolwidth = get_maxcolwidth(headers, wrap)
    style = get_style()
    for name, operator in ALL_OPERATORS.items():
        print(f"{name} operator:")
        if len(operator.cls.metrics) > 0:
            print(
                tabulate.tabulate(
                    headers=headers,
                    tabular_data=operator.cls.metrics,
                    tablefmt=style,
                    maxcolwidths=maxcolwidth,
                    maxheadercolwidths=maxcolwidth,
                )
            )
