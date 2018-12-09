"""
Halstead operator.

Measures all of the halstead metrics (volume, vocab, difficulty)
"""
import radon.cli.harvest as harvesters
from radon.cli import Config

from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


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
    }

    metrics = (
        Metric("h1", "h1 metric", int, MetricType.AimLow),
        Metric("h2", "h2 metric", int, MetricType.AimLow),
        Metric("N1", "N1 metric", int, MetricType.AimLow),
        Metric("N2", "N2 metric", int, MetricType.AimLow),
        Metric("vocabulary", "Unique vocabulary (h1 + h2)", int, MetricType.AimLow),
        Metric("length", "Length of application", int, MetricType.AimLow),
        Metric("volume", "Code volume", float, MetricType.AimLow),
        Metric("difficulity", "Difficulty", float, MetricType.AimLow),
        Metric("effort", "Effort", float, MetricType.AimLow),
    )

    default_metric_index = 0  # MI

    def __init__(self, config):
        """
        Instantiate a new HC operator.

        :param config: The wily configuration.
        :type  config: :class:`WilyConfig`
        """
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {config.targets} with {self.defaults} for HC metrics")

        self.harvester = harvesters.HCHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        """
        Run the operator.

        :param module: The target module path.
        :type  module: ``str``

        :param options: Any runtime options.
        :type  options: ``dict``

        :return: The operator results.
        :rtype: ``dict``
        """
        logger.debug("Running halstead harvester")
        results = {}
        for filename, details in dict(self.harvester.results).items():
            results[filename] = {}
            for instance in details:
                print(instance)
        return results
