import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


class MaintainabilityIndexOperator(BaseOperator):
    name = "maintainability"
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
        Metric("rank", "Maintainability Ranking", str, MetricType.Informational),
        Metric("mi", "Maintainability Index", float, MetricType.AimHigh),
    )

    default_metric_index = 1  # MI

    def __init__(self, config):
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {config.targets} with {self.defaults} for MI metrics")

        self.harvester = harvesters.MIHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
