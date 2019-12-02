"""
Raw statistics operator.

Includes insights like lines-of-code, number of comments. Does not measure complexity.
"""
import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


class RawMetricsOperator(BaseOperator):
    """Raw Metrics Operator."""

    name = "raw"
    defaults = {
        "exclude": None,
        "ignore": None,
        "summary": False,
        "include_ipynb": True,
        "ipynb_cells": True,
    }
    metrics = (
        Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
        Metric("lloc", "L Lines of Code", int, MetricType.AimLow, sum),
        Metric("sloc", "S Lines of Code", int, MetricType.AimLow, sum),
        Metric("comments", "Multi-line comments", int, MetricType.AimHigh, sum),
        Metric("multi", "Multi lines", int, MetricType.Informational, sum),
        Metric("blank", "blank lines", int, MetricType.Informational, sum),
        Metric(
            "single_comments",
            "Single comment lines",
            int,
            MetricType.Informational,
            sum,
        ),
    )
    default_metric_index = 0  # LOC

    def __init__(self, config, targets):
        """
        Instantiate a new raw operator.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`
        """
        # TODO: Use config from wily.cfg for harvester
        logger.debug(f"Using {targets} with {self.defaults} for Raw metrics")
        self.harvester = harvesters.RawHarvester(
            targets, config=Config(**self.defaults)
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
        logger.debug("Running raw harvester")
        results = {}
        for filename, metrics in dict(self.harvester.results).items():
            results[filename] = {"total": metrics}
        return results
