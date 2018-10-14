import radon.cli.harvest as harvestors
from radon.cli import Config

from wily.operators import BaseOperator


class RawMetricsOperator(BaseOperator):
    name = "raw"

    def __init__(self, config):
        # TODO: Use config from wily.cfg for harvestor
        self.harvestor = harvestors.RawHarvester(config.path, config=Config())

    def run(self, module, options):
        self.harvestor.run()
        return self.harvestor.results
