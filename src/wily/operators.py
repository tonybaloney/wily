"""Models and types for "operators" the basic measure of a module that measures code."""

from collections.abc import Iterable
from enum import Enum
from functools import lru_cache
from typing import (
    Any,
    Generic,
    TypeVar,
)

from wily.lang import _


class MetricType(Enum):
    """Type of metric, used in trends."""

    AimLow = 1  # Low is good, high is bad
    AimHigh = 2  # High is good, low is bad
    Informational = 3  # Doesn't matter


TValue = TypeVar("TValue")


class Metric(Generic[TValue]):
    """Represents a metric."""

    name: str
    description: str
    metric_type: TValue
    measure: MetricType

    def __init__(
        self,
        name: str,
        description: str,
        metric_type: TValue,
        measure: MetricType,
    ):
        """Initialise the metric."""
        self.name = name
        self.description = description
        self.metric_type = metric_type
        self.measure = measure


GOOD_STYLES = {
    MetricType.AimHigh: "green",
    MetricType.AimLow: "red",
    MetricType.Informational: "yellow",
}

BAD_STYLES = {
    MetricType.AimHigh: "red",
    MetricType.AimLow: "green",
    MetricType.Informational: "yellow",
}


class OperatorLevel(Enum):
    """Level of operator."""

    File = 1
    Object = 2


"""Type for an operator."""


class Operator:
    """Operator holder."""

    name: str
    description: str
    level: OperatorLevel

    def __init__(
        self,
        name: str,
        description: str,
        level: OperatorLevel = OperatorLevel.File,
    ):
        """Initialise the operator."""
        self.name = name
        self.description = description
        self.level = level



OPERATOR_CYCLOMATIC = Operator(
    name="cyclomatic",
    description=_("Cyclomatic Complexity of modules"),
    level=OperatorLevel.Object,
)

OPERATOR_RAW = Operator(
    name="raw",
    description=_("Raw Python statistics"),
    level=OperatorLevel.File,
)

OPERATOR_MAINTAINABILITY = Operator(
    name="maintainability",
    description=_("Maintainability index (lines of code and branching)"),
    level=OperatorLevel.File,
)

OPERATOR_HALSTEAD = Operator(
    name="halstead",
    description=_("Halstead metrics"),
    level=OperatorLevel.Object,
)


_OPERATORS: tuple[Operator, ...] = (
    OPERATOR_CYCLOMATIC,
    OPERATOR_MAINTAINABILITY,
    OPERATOR_RAW,
    OPERATOR_HALSTEAD,
)

OPERATOR_METRICS = {
    OPERATOR_CYCLOMATIC: (
        Metric(
            "complexity",
            _("Cyclomatic Complexity"),
            float,
            MetricType.AimLow,
        ),
    ),
    OPERATOR_RAW: (
        Metric("loc", _("Lines of Code"), int, MetricType.Informational),
        Metric("lloc", _("L Lines of Code"), int, MetricType.AimLow),
        Metric("sloc", _("S Lines of Code"), int, MetricType.AimLow),
        Metric("comments", _("Multi-line comments"), int, MetricType.AimHigh),
        Metric("multi", _("Multi lines"), int, MetricType.Informational),
        Metric("blank", _("blank lines"), int, MetricType.Informational),
        Metric(
            "single_comments",
            _("Single comment lines"),
            int,
            MetricType.Informational,
        ),
    ),
    OPERATOR_HALSTEAD:  (
        Metric("h1", _("Unique Operators"), int, MetricType.AimLow),
        Metric("h2", _("Unique Operands"), int, MetricType.AimLow),
        Metric("N1", _("Number of Operators"), int, MetricType.AimLow),
        Metric("N2", _("Number of Operands"), int, MetricType.AimLow),
        Metric("vocabulary", _("Unique vocabulary (h1 + h2)"), int, MetricType.AimLow),
        Metric("length", _("Length of application"), int, MetricType.AimLow),
        Metric("volume", _("Code volume"), float, MetricType.AimLow),
        Metric("difficulty", _("Difficulty"), float, MetricType.AimLow),
        Metric("effort", _("Effort"), float, MetricType.AimLow),
    ),
    OPERATOR_MAINTAINABILITY:  (
        Metric("rank", _("Maintainability Ranking"), str, MetricType.Informational),
        Metric("mi", _("Maintainability Index"), float, MetricType.AimHigh),
    )
}

"""Dictionary of all operators"""
ALL_OPERATORS: dict[str, Operator] = {operator.name: operator for operator in _OPERATORS}


"""Set of all metrics"""
ALL_METRICS: set[tuple[Operator, Metric[Any]]] = {(operator, metric) for operator in ALL_OPERATORS.values() for metric in OPERATOR_METRICS[operator]}


@lru_cache(maxsize=128)
def resolve_operator(name: str) -> Operator:
    """
    Get the :namedtuple:`wily.operators.Operator` for a given name.

    :param name: The name of the operator
    :return: The operator type
    """
    if name.lower() in ALL_OPERATORS:
        return ALL_OPERATORS[name.lower()]
    else:
        raise ValueError(f"Operator {name} not recognised.")


def resolve_operators(operators: Iterable[Operator | str]) -> list[Operator]:
    """Resolve a list of operator names to their corresponding types."""
    return [resolve_operator(operator) for operator in iter(operators)]


@lru_cache(maxsize=128)
def resolve_metric(metric: str) -> Metric:
    """Resolve metric key to a given target."""
    return resolve_metric_as_tuple(metric)[1]


@lru_cache(maxsize=128)
def resolve_metric_as_tuple(metric: str) -> tuple[Operator, Metric]:
    """Resolve metric key to a given target."""
    if "." in metric:
        _, metric = metric.split(".")

    r = [(operator, match) for operator, match in ALL_METRICS if match.name == metric]
    if not r or len(r) == 0:
        raise ValueError(f"Metric {metric} not recognised.")
    else:
        return r[0]


def get_metric(revision: dict[Any, Any], operator: str, path: str, key: str) -> Any:
    """
    Get a metric from the cache.

    :param revision: The revision data.
    :param operator: The operator name.
    :param path: The path to the file/function
    :param key: The key of the data
    :return: Data from the cache
    """
    if ":" in path:
        part, entry = path.split(":")
        val = revision[operator][part]["detailed"][entry][key]
    else:
        val = revision[operator][path]["total"][key]
    return val
