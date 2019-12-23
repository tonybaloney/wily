"""
Maintainability operator.

Measures the "maintainability" using the Halstead index.
"""
import statistics
from collections import Counter

import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


def mode(data):
    """
    Return the modal value of a iterable with discrete values.
    
    If there is more than 1 modal value, arbritrarily return the first top n.
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
        Metric("rank", "Maintainability Ranking", str, MetricType.Informational, mode),
        Metric(
            "mi", "Maintainability Index", float, MetricType.AimHigh, statistics.mean
        ),
    )

    default_metric_index = 1  # MI

    def __init__(self, config, targets):
        """
        Instantiate a new MI operator.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`
        """
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {targets} with {self.defaults} for MI metrics")

        self.harvester = harvesters.MIHarvester(targets, config=Config(**self.defaults))

    def run(self, module, options):
        """
        Run the operator.

        :param module: The target module path.
        :type  module: ``str``

        :param options: Any runtime options.
        :type  options: ``dict``

        :return: The operator results.
        :rtype: ``dict``
        """
        logger.debug("Running maintainability harvester")
        results = {}
        for filename, metrics in dict(self.harvester.results).items():
            results[filename] = {"total": metrics}
        return results
