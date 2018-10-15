from wily.operators import ALL_OPERATORS
from wily.config import DEFAULT_GRID_STYLE
import tabulate


def list_metrics():
    for operator in ALL_OPERATORS:
        print(f"{operator.name} operator:")
        if len(operator.cls.metrics) > 0 :
            print(
                tabulate.tabulate(
                    headers=("Name", "Description", "Type"), 
                    tabular_data=operator.cls.metrics,
                    tablefmt=DEFAULT_GRID_STYLE
                )
            )
        else:
            print("No metrics available")
