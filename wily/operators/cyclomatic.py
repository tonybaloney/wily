"""
Cyclomatic complexity metric for each function/method

Provided by the radon library

TODO : Figure out how to deal with the list metrics for functions?
"""

import radon.cli.harvest as harvesters
from radon.cli import Config
import radon
from radon.visitors import Function, Class
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
        import pdb

        pdb.set_trace()
        for filename, details in dict(self.harvester.results).items():
            results[filename] = {}
            for instance in details:
                if isinstance(instance, Class):
                    i = self._dict_from_class(instance)
                elif isinstance(instance, Function):
                    i = self._dict_from_class(instance)
                else:
                    raise TypeError("unexpected type : {type(instance)}")
                results[filename][i["fullname"]] = i

    @staticmethod
    def _dict_from_function(l):
        return {
            "name": l.name,
            "is_method": l.is_method,
            "classname": l.classname,
            "fullname": l.fullname,
            "closures": l.closures,
            "complexity": l.complexity,
        }

    @staticmethod
    def _dict_from_class(l):
        return {
            "name": l.name,
            "methods": l.methods,
            "fullname": l.fullname,
            "inner_classes": l.inner_classes,
            "real_complexity": l.real_complexity,
            "complexity": l.complexity,
        }
