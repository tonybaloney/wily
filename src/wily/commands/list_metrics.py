"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""

import tabulate

from wily.helper import get_style
from wily.operators import ALL_OPERATORS


def list_metrics():
    """List metrics available."""
    style = get_style()

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
