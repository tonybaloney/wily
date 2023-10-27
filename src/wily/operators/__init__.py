"""Models and types for "operators" the basic measure of a module that measures code."""

from enum import Enum
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from wily.config.types import WilyConfig
from wily.lang import _


class MetricType(Enum):
    """Type of metric, used in trends."""

    AimLow = 1  # Low is good, high is bad
    AimHigh = 2  # High is good, low is bad
    Informational = 3  # Doesn't matter


TValue = TypeVar("TValue", str, int, float)


class Metric(Generic[TValue]):
    """Represents a metric."""

    name: str
    description: str
    metric_type: TValue
    measure: MetricType
    aggregate: Callable[[Iterable[TValue]], TValue]

    def __init__(
        self,
        name: str,
        description: str,
        metric_type: TValue,
        measure: MetricType,
        aggregate: Callable[[Iterable[TValue]], TValue],
    ):
        """Initialise the metric."""
        self.name = name
        self.description = description
        self.metric_type = metric_type
        self.measure = measure
        self.aggregate = aggregate


GOOD_COLORS = {
    MetricType.AimHigh: 32,
    MetricType.AimLow: 31,
    MetricType.Informational: 33,
}

BAD_COLORS = {
    MetricType.AimHigh: 31,
    MetricType.AimLow: 32,
    MetricType.Informational: 33,
}


class OperatorLevel(Enum):
    """Level of operator."""

    File = 1
    Object = 2


class BaseOperator:
    """Abstract Operator Class."""

    """Name of the operator."""
    name: str = "abstract"

    """Default settings."""
    defaults: Dict[str, Any] = {}

    """Available metrics as a list of tuple ("name"<str>, "description"<str>, "type"<type>, "metric_type"<MetricType>)."""
    metrics: Tuple[Metric, ...] = ()

    """Which metric is the default to display in the report command."""
    default_metric_index: Optional[int] = None

    """Level at which the operator goes to."""
    level: OperatorLevel = OperatorLevel.File

    def __init__(self, *args, **kwargs):
        """Initialise the operator."""
        ...

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        raise NotImplementedError


from wily.operators.cyclomatic import CyclomaticComplexityOperator
from wily.operators.halstead import HalsteadOperator
from wily.operators.maintainability import MaintainabilityIndexOperator
from wily.operators.raw import RawMetricsOperator

"""Type for an operator."""

T = TypeVar("T", bound=BaseOperator)


class Operator(Generic[T]):
    """Operator holder."""

    name: str
    operator_cls: Type[T]
    description: str
    level: OperatorLevel

    def __init__(
        self,
        name: str,
        operator_cls: Type[T],
        description: str,
        level: OperatorLevel = OperatorLevel.File,
    ):
        """Initialise the operator."""
        self.name = name
        self.operator_cls = operator_cls
        self.description = description
        self.level = level

    def __call__(self, config: "WilyConfig") -> T:
        """Initialise the operator."""
        return self.operator_cls(config)


OPERATOR_CYCLOMATIC = Operator(
    name="cyclomatic",
    operator_cls=CyclomaticComplexityOperator,
    description=_("Cyclomatic Complexity of modules"),
    level=OperatorLevel.Object,
)

OPERATOR_RAW = Operator(
    name="raw",
    operator_cls=RawMetricsOperator,
    description=_("Raw Python statistics"),
    level=OperatorLevel.File,
)

OPERATOR_MAINTAINABILITY = Operator(
    name="maintainability",
    operator_cls=MaintainabilityIndexOperator,
    description=_("Maintainability index (lines of code and branching)"),
    level=OperatorLevel.File,
)

OPERATOR_HALSTEAD = Operator(
    name="halstead",
    operator_cls=HalsteadOperator,
    description=_("Halstead metrics"),
    level=OperatorLevel.Object,
)


_OPERATORS: Tuple[Operator, ...] = (
    OPERATOR_CYCLOMATIC,
    OPERATOR_MAINTAINABILITY,
    OPERATOR_RAW,
    OPERATOR_HALSTEAD,
)
"""Dictionary of all operators"""
ALL_OPERATORS: Dict[str, Operator] = {
    operator.name: operator for operator in _OPERATORS
}


"""Set of all metrics"""
ALL_METRICS: Set[Tuple[Operator, Metric[Any]]] = {
    (operator, metric)
    for operator in ALL_OPERATORS.values()
    for metric in operator.operator_cls.metrics
}


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


def resolve_operators(operators: Iterable[Union[Operator, str]]) -> List[Operator]:
    """Resolve a list of operator names to their corresponding types."""
    return [resolve_operator(operator) for operator in iter(operators)]


@lru_cache(maxsize=128)
def resolve_metric(metric: str) -> Metric:
    """Resolve metric key to a given target."""
    return resolve_metric_as_tuple(metric)[1]


@lru_cache(maxsize=128)
def resolve_metric_as_tuple(metric: str) -> Tuple[Operator, Metric]:
    """Resolve metric key to a given target."""
    if "." in metric:
        _, metric = metric.split(".")

    r = [(operator, match) for operator, match in ALL_METRICS if match.name == metric]
    if not r or len(r) == 0:
        raise ValueError(f"Metric {metric} not recognised.")
    else:
        return r[0]


def get_metric(revision: Dict[Any, Any], operator: str, path: str, key: str) -> Any:
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
