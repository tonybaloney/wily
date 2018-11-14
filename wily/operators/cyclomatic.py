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
        results = {}
        # TODO : Recursive.
        for filename, details in dict(self.harvester.results).items():
            logger.debug(details)
            if len(details) == 8:
                results[filename] = self._dict_from_function(details)
            elif len(details) == 7:
                results[filename] = self._dict_from_class(details)

    @staticmethod
    def _dict_from_function(l):
        return {
            "name": l[0],
            "lineno": l[1],
            "col_offset": l[2],
            "endline": l[3],
            "is_method": l[4],
            "classname": l[5],
            "closures": l[6],
            "complexity": l[7],
        }

    @staticmethod
    def _dict_from_class(l):
        return {
            "name": l[0],
            "lineno": l[1],
            "col_offset": l[2],
            "endline": l[3],
            "methods": l[4],
            "inner_classes": l[5],
            "real_complexity": l[6],
        }
