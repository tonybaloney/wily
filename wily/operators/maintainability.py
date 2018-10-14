import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator


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

    def __init__(self, config):
        # TODO : Import config from wily.cfg
        logger.debug(f"Using {config.path} with {self.defaults} for MI metrics")

        self.harvester = harvesters.MIHarvester(
            [config.path], config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
