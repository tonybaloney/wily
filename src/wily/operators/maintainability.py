"""
Maintainability operator.

Measures the "maintainability" using the Halstead index.
"""
import statistics
from collections import Counter
from typing import Any, Dict, Iterable

import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


def mode(data):
    """
    Return the modal value of an iterable with discrete values.

    If there is more than 1 modal value, arbitrarily return the first top n.
    """
    c = Counter(data)
    mode, freq = c.most_common(1)[0]
    return mode


class MaintainabilityIndexOperator(BaseOperator):
    """MI Operator."""

    name = "maintainability"
    defaults = {
        "exclude": None,
        "ignore": None,
        "min": "A",
        "max": "C",
        "multi": True,
        "show": False,
        "sort": False,
        "include_ipynb": True,
        "ipynb_cells": True,
    }

    metrics = (
        Metric(
            "rank", _("Maintainability Ranking"), str, MetricType.Informational, mode
        ),
        Metric(
            "mi", _("Maintainability Index"), float, MetricType.AimHigh, statistics.mean
        ),
    )

    default_metric_index = 1  # MI

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new MI operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        # TODO : Import config from wily.cfg
        logger.debug("Using %s with %s for MI metrics", targets, self.defaults)

        self.harvester = harvesters.MIHarvester(targets, config=Config(**self.defaults))

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running maintainability harvester")
        results = {}
        for filename, metrics in dict(self.harvester.results).items():
            results[filename] = {"total": metrics}
        return results
