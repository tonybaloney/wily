"""
Halstead operator.

Measures all of the halstead metrics (volume, vocab, difficulty)

Uses the Rust parser backend for performance.
"""

from collections.abc import Iterable
from typing import Any

from wily import logger
from wily.backend import harvest_halstead_metrics
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
        Metric("h1", _("Unique Operators"), int, MetricType.AimLow, sum),
        Metric("h2", _("Unique Operands"), int, MetricType.AimLow, sum),
        Metric("N1", _("Number of Operators"), int, MetricType.AimLow, sum),
        Metric("N2", _("Number of Operands"), int, MetricType.AimLow, sum),
        Metric("vocabulary", _("Unique vocabulary (h1 + h2)"), int, MetricType.AimLow, sum),
        Metric("length", _("Length of application"), int, MetricType.AimLow, sum),
        Metric("volume", _("Code volume"), float, MetricType.AimLow, sum),
        Metric("difficulty", _("Difficulty"), float, MetricType.AimLow, sum),
        Metric("effort", _("Effort"), float, MetricType.AimLow, sum),
    )

    default_metric_index = 0  # h1

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new Halstead operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        logger.debug("Using %s with %s for Halstead metrics", targets, self.defaults)
        self._targets = tuple(targets)
        self._exclude = self.defaults.get("exclude") or None
        self._ignore = self.defaults.get("ignore") or None

    def run(self, module: str, options: dict[str, Any]) -> dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running halstead harvester via Rust")

        sources, errors = self._collect_sources()
        results: dict[str, dict[str, Any]] = {}

        if sources:
            rust_results = dict(harvest_halstead_metrics(sources))
            for filename, details in rust_results.items():
                if "error" in details:
                    logger.debug(
                        "Failed to run halstead harvester on %s : %s",
                        filename,
                        details["error"],
                    )
                    results[filename] = {"detailed": {}, "total": self._empty_metrics()}
                    continue

                results[filename] = {"detailed": {}, "total": {}}

                # Process total metrics
                total = details.get("total", {})
                results[filename]["total"] = self._metrics_to_dict(total)

                # Process function metrics
                functions = details.get("functions", {})
                for func_name, func_metrics in functions.items():
                    results[filename]["detailed"][func_name] = self._metrics_to_dict(func_metrics)

        for filename, error_payload in errors.items():
            results[filename] = {"detailed": {}, "total": error_payload}

        return results

    @staticmethod
    def _metrics_to_dict(metrics: dict[str, Any]) -> dict[str, Any]:
        """Convert Rust metrics dict to wily format."""
        return {
            "h1": metrics.get("h1", 0),
            "h2": metrics.get("h2", 0),
            "N1": metrics.get("N1", 0),
            "N2": metrics.get("N2", 0),
            "vocabulary": metrics.get("vocabulary", 0),
            "volume": metrics.get("volume", 0.0),
            "length": metrics.get("length", 0),
            "effort": metrics.get("effort", 0.0),
            "difficulty": metrics.get("difficulty", 0.0),
            "lineno": metrics.get("lineno"),
            "endline": metrics.get("endline"),
        }

    @staticmethod
    def _empty_metrics() -> dict[str, Any]:
        """Return empty metrics dict for error cases."""
        return {
            "h1": 0,
            "h2": 0,
            "N1": 0,
            "N2": 0,
            "vocabulary": 0,
            "volume": 0.0,
            "length": 0,
            "effort": 0.0,
            "difficulty": 0.0,
            "lineno": None,
            "endline": None,
        }
