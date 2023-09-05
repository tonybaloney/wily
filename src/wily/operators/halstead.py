"""
Halstead operator.

Measures all of the halstead metrics (volume, vocab, difficulty)
"""
from typing import Any, Dict, Iterable

import radon.cli.harvest as harvesters
from radon.cli import Config
from radon.metrics import HalsteadReport

from wily import logger
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


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
        Metric("h1", _("Unique Operands"), int, MetricType.AimLow, sum),
        Metric("h2", _("Unique Operators"), int, MetricType.AimLow, sum),
        Metric("N1", _("Number of Operands"), int, MetricType.AimLow, sum),
        Metric("N2", _("Number of Operators"), int, MetricType.AimLow, sum),
        Metric(
            "vocabulary", _("Unique vocabulary (h1 + h2)"), int, MetricType.AimLow, sum
        ),
        Metric("length", _("Length of application"), int, MetricType.AimLow, sum),
        Metric("volume", _("Code volume"), float, MetricType.AimLow, sum),
        Metric("difficulty", _("Difficulty"), float, MetricType.AimLow, sum),
        Metric("effort", _("Effort"), float, MetricType.AimLow, sum),
    )

    default_metric_index = 0  # MI

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new HC operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {targets} with {self.defaults} for HC metrics")

        self.harvester = harvesters.HCHarvester(targets, config=Config(**self.defaults))

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running halstead harvester")
        results = {}
        for filename, details in dict(self.harvester.results).items():
            results[filename] = {"detailed": {}, "total": {}}
            for instance in details:
                if isinstance(instance, list):
                    for item in instance:
                        function, report = item
                        assert isinstance(report, HalsteadReport)
                        results[filename]["detailed"][function] = self._report_to_dict(
                            report
                        )
                else:
                    if isinstance(instance, str) and instance == "error":
                        logger.debug(
                            f"Failed to run Halstead harvester on {filename} : {details['error']}"
                        )
                        continue
                    assert isinstance(instance, HalsteadReport)
                    results[filename]["total"] = self._report_to_dict(instance)
        return results

    def _report_to_dict(self, report: HalsteadReport) -> Dict[str, Any]:
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
