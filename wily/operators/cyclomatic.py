import radon.cli.harvest as harvestors
from radon.cli import Config

from wily.operators import BaseOperator


class CyclomaticComplexityOperator(BaseOperator):
    name = "cyclomatic"
    defaults = {
        "exclude": [],
        "ignore": ""
    }

    def __init__(self, config):
        # TODO: Import config for harvestor from .wily.cfg
        self.harvestor = harvestors.CCHarvester(config.path, config=Config(**self.defaults))

    def run(self, module, options):
        self.harvestor.run()
        return self.harvestor.as_json()
