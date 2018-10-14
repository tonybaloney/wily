import radon.cli.harvest as harvestors
from radon.cli import Config

from wily.operators import BaseOperator


class MaintainabilityIndexOperator(BaseOperator):
    name = "maintainability"

    def __init__(self, config):
        # TODO : Import config from wily.cfg
        self.harvestor = harvestors.MIHarvester(config.path, config=Config())

    def run(self, module, options):
        self.harvestor.run()
        return self.harvestor.results
