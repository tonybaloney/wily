"""
Cyclomatic complexity metric for each function/method.

Uses the Rust parser backend for performance.
"""

import statistics
from collections.abc import Iterable
from typing import Any

from wily import logger
from wily.backend import harvest_cyclomatic_metrics
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


class CyclomaticComplexityOperator(BaseOperator):
    """Cyclomatic complexity operator."""

    name = "cyclomatic"
    defaults = {
        "exclude": None,
        "ignore": None,
        "min": "A",
        "max": "F",
        "no_assert": True,
        "show_closures": False,
        "order": lambda x: -x.complexity,
        "include_ipynb": True,
        "ipynb_cells": True,
    }

    metrics = (
        Metric(
            "complexity",
            _("Cyclomatic Complexity"),
            float,
            MetricType.AimLow,
            statistics.mean,
        ),
    )

    default_metric_index = 0  # MI

    def __init__(self, config: WilyConfig, targets: Iterable[str]):
        """
        Instantiate a new Cyclomatic Complexity operator.

        :param config: The wily configuration.
        :param targets: An iterable of paths from which to harvest metrics.
        """
        logger.debug("Using %s with %s for CC metrics", targets, self.defaults)
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
        logger.debug("Running CC harvester via Rust")

        sources, errors = self._collect_sources()
        results: dict[str, dict[str, Any]] = {}

        if sources:
            rust_results = dict(harvest_cyclomatic_metrics(sources))
            for filename, details in rust_results.items():
                if "error" in details:
                    logger.debug(
                        "Failed to run CC harvester on %s : %s",
                        filename,
                        details["error"],
                    )
                    results[filename] = {"detailed": {}, "total": {"complexity": 0}}
                    continue

                results[filename] = {"detailed": {}, "total": {}}
                total = 0  # running CC total

                # Process functions (includes methods from classes)
                for func in details.get("functions", []):
                    i = self._dict_from_function(func)
                    results[filename]["detailed"][i["fullname"]] = i
                    del i["fullname"]
                    total += i["complexity"]

                # Process classes
                for cls in details.get("classes", []):
                    i = self._dict_from_class(cls)
                    results[filename]["detailed"][i["fullname"]] = i
                    del i["fullname"]
                    total += i["complexity"]

                results[filename]["total"]["complexity"] = total

        for filename, error_payload in errors.items():
            results[filename] = {"detailed": {}, "total": error_payload}

        return results

    @staticmethod
    def _dict_from_function(f: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": f["name"],
            "is_method": f["is_method"],
            "classname": f["classname"],
            "closures": f.get("closures", []),
            "complexity": f["complexity"],
            "fullname": f["fullname"],
            "loc": f["endline"] - f["lineno"],
            "lineno": f["lineno"],
            "endline": f["endline"],
        }

    @staticmethod
    def _dict_from_class(c: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": c["name"],
            "inner_classes": c.get("inner_classes", []),
            "real_complexity": c["real_complexity"],
            "complexity": c["complexity"],
            "fullname": c["fullname"],
            "loc": c["endline"] - c["lineno"],
            "lineno": c["lineno"],
            "endline": c["endline"],
        }
