"""Raw statistics operator built on top of the Rust parser backend."""
from typing import Any, Dict, Iterable, List, Tuple

import radon.cli.harvest as harvesters
from radon.cli import Config
from radon.cli.tools import _open, iter_filenames

from wily import (
    logger,
)
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType

import wily._rust as rust_backend


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
        self._radon_config = Config(**self.defaults)
        self.harvester = harvesters.RawHarvester(
            self._targets, config=self._radon_config
        )

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running raw harvester via Wily")
        return self._run_with_rust()


    def _run_with_rust(self) -> Dict[Any, Any]:
        logger.debug("Running raw harvester via Rust backend")
        sources, errors = self._collect_sources()
        results: Dict[Any, Any] = {}

        if sources:
            rust_payload = rust_backend.rust_harvest_raw_metrics(sources)
            for filename, metrics in rust_payload.items():
                results[filename] = {"total": metrics}

        for filename, error_payload in errors.items():
            results[filename] = {"total": error_payload}

        return results

    def _collect_sources(self) -> Tuple[List[Tuple[str, str]], Dict[str, Dict[str, str]]]:
        sources: List[Tuple[str, str]] = []
        errors: Dict[str, Dict[str, str]] = {}
        for name in iter_filenames(
            self._targets, self._radon_config.exclude, self._radon_config.ignore
        ):
            try:
                with _open(name) as fobj:
                    sources.append((name, fobj.read()))
            except Exception as exc:  # pragma: no cover - depends on filesystem state
                errors[name] = {"error": str(exc)}

        return sources, errors
