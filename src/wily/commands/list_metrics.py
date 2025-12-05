"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""

from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.operators import OPERATOR_METRICS


def list_metrics(wrap: bool, table_style: str = DEFAULT_TABLE_STYLE) -> None:
    """
    List metrics available.

    :param wrap: Wrap output
    :param table_style: Table box style
    """
    headers = ("Name", "Description", "Type", "Measure")
    for operator, metrics in OPERATOR_METRICS.items():
        print(f"{operator.name} operator:")
        if len(metrics) > 0:
            data = [
                (
                    m.name,
                    m.description,
                    m.metric_type.__name__,
                    m.measure,
                )
                for m in metrics
            ]
            print_table(headers=headers, data=data, wrap=wrap, table_style=table_style)
