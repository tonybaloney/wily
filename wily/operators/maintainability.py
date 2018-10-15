import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator, MetricType


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
        ("rank", "Maintainability Ranking", str, MetricType.Informational),
        ("mi", "Maintainability Index", float, MetricType.AimLow)
    )

    def __init__(self, config):
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {config.targets} with {self.defaults} for MI metrics")

        self.harvester = harvesters.MIHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
