"""
Maintainability operator.

Measures the "maintainability" using the Maintainability Index.

Uses the Rust parser backend for performance.
"""

import statistics
from typing import Any, Dict, Iterable, List, Tuple

from wily._rust import iter_filenames

from wily import logger
from wily._rust import harvest_maintainability_metrics
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

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running maintainability harvester via Rust")

        sources, errors = self._collect_sources()
        results: Dict[str, Dict[str, Any]] = {}

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

    def _collect_sources(self) -> Tuple[List[Tuple[str, str]], Dict[str, Dict[str, str]]]:
        """Collect source files and their contents."""
        sources: List[Tuple[str, str]] = []
        errors: Dict[str, Dict[str, str]] = {}
        for name in iter_filenames(self._targets, self._exclude, self._ignore):
            try:
                with open(name, encoding="utf-8") as fobj:
                    sources.append((name, fobj.read()))
            except Exception as exc:  # pragma: no cover - depends on filesystem state
                errors[name] = {"error": str(exc)}

        return sources, errors
