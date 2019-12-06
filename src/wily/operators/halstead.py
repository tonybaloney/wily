"""
Halstead operator.

Measures all of the halstead metrics (volume, vocab, difficulty)
"""
import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


class HalsteadOperator(BaseOperator):
    """Halstead Operator."""

    name = "halstead"
    defaults = {
        "exclude": None,
        "ignore": None,
        "min": "A",
        "max": "C",
        "multi": True,
        "show": False,
        "sort": False,
        "by_function": True,
        "include_ipynb": True,
        "ipynb_cells": True,
    }

    metrics = (
        Metric("h1", "Unique Operands", int, MetricType.AimLow, sum),
        Metric("h2", "Unique Operators", int, MetricType.AimLow, sum),
        Metric("N1", "Number of Operands", int, MetricType.AimLow, sum),
        Metric("N2", "Number of Operators", int, MetricType.AimLow, sum),
        Metric(
            "vocabulary", "Unique vocabulary (h1 + h2)", int, MetricType.AimLow, sum
        ),
        Metric("length", "Length of application", int, MetricType.AimLow, sum),
        Metric("volume", "Code volume", float, MetricType.AimLow, sum),
        Metric("difficulty", "Difficulty", float, MetricType.AimLow, sum),
        Metric("effort", "Effort", float, MetricType.AimLow, sum),
    )

    default_metric_index = 0  # MI

    def __init__(self, config, targets):
        """
        Instantiate a new HC operator.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`
        """
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {targets} with {self.defaults} for HC metrics")

        self.harvester = harvesters.HCHarvester(targets, config=Config(**self.defaults))

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
        logger.debug("Running halstead harvester")
        results = {}
        for filename, details in dict(self.harvester.results).items():
            results[filename] = {"detailed": {}, "total": {}}
            for instance in details:
                if isinstance(instance, list):
                    for item in instance:
                        function, report = item
                        results[filename]["detailed"][function] = self._report_to_dict(
                            report
                        )
                else:
                    if isinstance(instance, str) and instance == "error":
                        logger.debug(
                            f"Failed to run Halstead harvester on {filename} : {details['error']}"
                        )
                        continue
                    results[filename]["total"] = self._report_to_dict(instance)
        return results

    def _report_to_dict(self, report):
        return {
            "h1": report.h1,
            "h2": report.h2,
            "N1": report.N1,
            "N2": report.N2,
            "vocabulary": report.vocabulary,
            "volume": report.volume,
            "length": report.length,
            "effort": report.effort,
            "difficulty": report.difficulty,
        }
