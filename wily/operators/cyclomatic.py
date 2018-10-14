import radon.cli.harvest as harvestors
from radon.cli import Config

from wily.operators import BaseOperator


class CyclomaticComplexityOperator(BaseOperator):
    name = "cyclomatic"

    def __init__(self, config):
        # TODO: Import config for harvestor from .wily.cfg
        self.harvestor = harvestors.CCHarvester(config.path, config=Config())

    def run(self, module, options):
        self.harvestor.run()
        return self.harvestor.results
