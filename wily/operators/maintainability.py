"""
Maintainability operator.

Measures the "maintainability" using the Halstead index.
"""
import statistics

import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


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
    }

    metrics = (
        Metric(
            "rank",
            "Maintainability Ranking",
            str,
            MetricType.Informational,
            statistics.mode,
        ),
        Metric(
            "mi", "Maintainability Index", float, MetricType.AimLow, statistics.mean
        ),
    )

    default_metric_index = 1  # MI

    def __init__(self, config):
        """
        Instantiate a new MI operator.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`
        """
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {config.targets} with {self.defaults} for MI metrics")

        self.harvester = harvesters.MIHarvester(
            config.targets, config=Config(**self.defaults)
        )

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
        return dict(self.harvester.results)
