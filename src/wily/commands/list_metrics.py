"""
List available metrics across all providers.

TODO : Only show metrics for the operators that the cache has?
"""
import tabulate

from wily.helper import get_maxcolwidth, get_style
from wily.operators import ALL_OPERATORS


def list_metrics(wrap: bool) -> None:
    """List metrics available."""
    headers = ("Name", "Description", "Type", "Measure", "Aggregate")
    maxcolwidth = get_maxcolwidth(headers, wrap)
    style = get_style()
    for name, operator in ALL_OPERATORS.items():
        print(f"{name} operator:")
        if len(operator.operator_cls.metrics) > 0:
            print(
                tabulate.tabulate(
                    headers=headers,
                    tabular_data=[
                        (
                            m.name,
                            m.description,
                            m.metric_type.__name__,
                            m.measure,
                            m.aggregate.__name__,
                        )
                        for m in operator.operator_cls.metrics
                    ],
                    tablefmt=style,
                    maxcolwidths=maxcolwidth,
                    maxheadercolwidths=maxcolwidth,
                )
            )
