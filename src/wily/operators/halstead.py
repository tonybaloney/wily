"""
Halstead operator.

Measures all of the halstead metrics (volume, vocab, difficulty)
"""
import ast
import collections
from typing import Any, Dict, Iterable

import radon.cli.harvest as harvesters
from radon.cli import Config
from radon.metrics import Halstead, HalsteadReport, halstead_visitor_report
from radon.visitors import HalsteadVisitor

from wily import logger
from wily.config.types import WilyConfig
from wily.lang import _
from wily.operators import BaseOperator, Metric, MetricType

NumberedHalsteadReport = collections.namedtuple(
    "NumberedHalsteadReport",
    HalsteadReport._fields + ("lineno", "endline"),
)


class NumberedHalsteadVisitor(HalsteadVisitor):
    """HalsteadVisitor that adds class name, lineno and endline for code blocks."""

    def __init__(self, context=None, lineno=None, endline=None, classname=None):
        """
        Initialize the numbered visitor.

        :param context: Function/method name.
        :param lineno: The starting line of the code block, if any.
        :param endline: The ending line of the code block, if any.
        :param classname: The class name for a method.
        """
        super().__init__(context)
        self.lineno = lineno
        self.endline = endline
        self.class_name = classname

    def visit_FunctionDef(self, node):
        """Visit functions and methods, adding class name if any, lineno and endline."""
        if self.class_name:
            node.name = f"{self.class_name}.{node.name}"
        super().visit_FunctionDef(node)
        self.function_visitors[-1].lineno = node.lineno
        # FuncDef is missing end_lineno in Python 3.7
        endline = node.end_lineno if hasattr(node, "end_lineno") else None
        self.function_visitors[-1].endline = endline

    def visit_ClassDef(self, node):
        """Visit classes, adding class name and creating visitors for methods."""
        self.class_name = node.name
        for child in node.body:
            visitor = NumberedHalsteadVisitor(classname=self.class_name)
            visitor.visit(child)
            self.function_visitors.extend(visitor.function_visitors)
        self.class_name = None


def number_report(visitor):
    """Create a report with added lineno and endline."""
    return NumberedHalsteadReport(
        *(halstead_visitor_report(visitor) + (visitor.lineno, visitor.endline))
    )


class NumberedHCHarvester(harvesters.HCHarvester):
    """Version of HCHarvester that adds lineno and endline."""

    def gobble(self, fobj):
        """Analyze the content of the file object, adding line numbers for blocks."""
        code = fobj.read()
        visitor = NumberedHalsteadVisitor.from_ast(ast.parse(code))
        total = number_report(visitor)
        functions = [(v.context, number_report(v)) for v in visitor.function_visitors]
        return Halstead(total, functions)


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
        logger.debug("Using %s with %s for HC metrics", targets, self.defaults)

        self.harvester = NumberedHCHarvester(targets, config=Config(**self.defaults))

    def run(self, module: str, options: Dict[str, Any]) -> Dict[Any, Any]:
        """
        Run the operator.

        :param module: The target module path.
        :param options: Any runtime options.
        :return: The operator results.
        """
        logger.debug("Running halstead harvester")
        results: Dict[str, Dict[str, Any]] = {}
        for filename, details in dict(self.harvester.results).items():
            results[filename] = {"detailed": {}, "total": {}}
            for instance in details:
                if isinstance(instance, list):
                    for item in instance:
                        function, report = item
                        assert isinstance(report, NumberedHalsteadReport)
                        results[filename]["detailed"][function] = self._report_to_dict(
                            report
                        )
                else:
                    if isinstance(instance, str) and instance == "error":
                        logger.debug(
                            "Failed to run Halstead harvester on %s : %s",
                            filename,
                            details["error"],
                        )
                        continue
                    assert isinstance(instance, NumberedHalsteadReport)
                    results[filename]["total"] = self._report_to_dict(instance)
        return results

    def _report_to_dict(self, report: NumberedHalsteadReport) -> Dict[str, Any]:
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
            "lineno": report.lineno,
            "endline": report.endline,
        }
