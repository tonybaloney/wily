import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator


class RawMetricsOperator(BaseOperator):
    name = "raw"
    defaults = {"exclude": None, "ignore": None, "summary": False}

    def __init__(self, config):
        # TODO: Use config from wily.cfg for harvester
        logger.debug(f"Using {config.path} with {self.defaults} for Raw metrics")
        self.harvester = harvesters.RawHarvester(
            [config.path], config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
