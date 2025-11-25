"""
Maintainability operator.

Measures the "maintainability" using the Maintainability Index.

Uses the Rust parser backend for performance.
"""

import statistics
from collections.abc import Iterable
from typing import Any

from wily import logger
from wily.backend import harvest_maintainability_metrics
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


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
        Metric("rank", _("Maintainability Ranking"), str, MetricType.Informational, statistics.mode),
        Metric("mi", _("Maintainability Index"), float, MetricType.AimHigh, statistics.mean),
    )

    default_metric_index = 1  # MI

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new MI operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        logger.debug("Using %s with %s for MI metrics", targets, self.defaults)
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
        logger.debug("Running maintainability harvester via Rust")

        sources, errors = self._collect_sources()
        results: dict[str, dict[str, Any]] = {}

        if sources:
            multi = self.defaults.get("multi", True)
            rust_results = dict(harvest_maintainability_metrics(sources, multi=multi))

            for filename, metrics in rust_results.items():
                if "error" in metrics:
                    logger.debug(
                        "Failed to run MI harvester on %s : %s",
                        filename,
                        metrics["error"],
                    )
                    results[filename] = {"total": {"mi": 0.0, "rank": "C"}}
                    continue

                results[filename] = {
                    "total": {
                        "mi": metrics["mi"],
                        "rank": metrics["rank"],
                    }
                }

        for filename, error_payload in errors.items():
            results[filename] = {"total": error_payload}

        return results
