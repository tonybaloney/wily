"""
List available metrics across all providers

TODO : Only show metrics for the operators that the cache has?
"""
from wily import logger
from wily.operators import ALL_OPERATORS
from wily.config import DEFAULT_GRID_STYLE
import tabulate


def list_metrics():
    for operator in ALL_OPERATORS:
        print(f"{operator.name} operator:")
        if len(operator.cls.metrics) > 0:
            print(
                tabulate.tabulate(
                    headers=("Name", "Description", "Type"),
                    tabular_data=operator.cls.metrics,
                    tablefmt=DEFAULT_GRID_STYLE,
                )
            )
