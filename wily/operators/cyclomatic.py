"""
Cyclomatic complexity metric for each function/method

Provided by the radon library

TODO : Figure out how to deal with the list metrics for functions?
"""

import radon.cli.harvest as harvesters
from radon.cli import Config
import radon
from wily import logger
from wily.operators import BaseOperator


class CyclomaticComplexityOperator(BaseOperator):
    name = "cyclomatic"
    defaults = {
        "exclude": None,
        "ignore": None,
        "min": "A",
        "max": "F",
        "no_assert": True,
        "show_closures": False,
        "order": radon.complexity.SCORE,
    }

    metrics = ()

    def __init__(self, config):
        # TODO: Import config for harvester from .wily.cfg
        logger.debug(f"Using {config.targets} with {self.defaults} for CC metrics")

        self.harvester = harvesters.CCHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running CC harvester")
        return dict(self.harvester.results)
