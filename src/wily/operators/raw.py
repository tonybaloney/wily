"""Raw statistics operator built on top of the Rust parser backend."""

from collections.abc import Iterable
from typing import Any, TypedDict

from wily import (
    logger,
)
from wily._rust import harvest_raw_metrics, iter_filenames
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType


class RawCounts(TypedDict):
    loc: int
    lloc: int
    sloc: int
    comments: int
    multi: int
    blank: int
    single_comments: int


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
        logger.debug("Running raw harvester via Wily")

        sources, errors = self._collect_sources()
        results: dict[Any, Any] = {}

        if sources:
            raw_counts: Iterable[tuple[str, RawCounts]] = harvest_raw_metrics(sources)
            for filename, metrics in raw_counts:
                results[filename] = {"total": metrics}

        for filename, error_payload in errors.items():
            results[filename] = {"total": error_payload}

        return results

    def _collect_sources(self) -> tuple[list[tuple[str, str]], dict[str, dict[str, str]]]:
        sources: list[tuple[str, str]] = []
        errors: dict[str, dict[str, str]] = {}
        for name in iter_filenames(self._targets, self._exclude, self._ignore):
            try:
                with open(name, encoding="utf-8") as fobj:
                    sources.append((name, fobj.read()))
            except Exception as exc:  # pragma: no cover - depends on filesystem state
                errors[name] = {"error": str(exc)}

        return sources, errors
