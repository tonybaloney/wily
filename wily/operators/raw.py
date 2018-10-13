import radon.cli.harvest as harvestors

from wily.operators import BaseOperator


class CyclomaticComplexityOperator(BaseOperator):
    def __init__(self, config):
        self.harvestor = harvestors.RawHarvester(config.path)

    def run(self, module, options):
        self.harvestor.run()
        return self.harvestor.results
