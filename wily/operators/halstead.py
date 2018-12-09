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
    }

    metrics = (
    )

    default_metric_index = None  # MI

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
        r = dict(self.harvester.results)
        import pdb; pdb.set_trace()
        return r
