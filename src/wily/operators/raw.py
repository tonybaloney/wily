"""
Raw statistics operator.

Includes insights like lines-of-code, number of comments. Does not measure complexity.
"""
from typing import Any, Dict, Iterable

import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


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
        Metric("loc", _("Lines of Code"), int, MetricType.Informational, sum),
        Metric("lloc", _("L Lines of Code"), int, MetricType.AimLow, sum),
        Metric("sloc", _("S Lines of Code"), int, MetricType.AimLow, sum),
        Metric("comments", _("Multi-line comments"), int, MetricType.AimHigh, sum),
        Metric("multi", _("Multi lines"), int, MetricType.Informational, sum),
        Metric("blank", _("blank lines"), int, MetricType.Informational, sum),
        Metric(
            "single_comments",
            _("Single comment lines"),
            int,
            MetricType.Informational,
            sum,
        ),
    )
    default_metric_index = 0  # LOC

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new raw operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        # TODO: Use config from wily.cfg for harvester
        logger.debug("Using %s with %s for Raw metrics", targets, self.defaults)
        self.harvester = harvesters.RawHarvester(
            targets, config=Config(**self.defaults)
        )

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running raw harvester")
        results = {}
        for filename, metrics in dict(self.harvester.results).items():
            results[filename] = {"total": metrics}
        return results
