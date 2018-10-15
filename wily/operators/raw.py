import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator


class RawMetricsOperator(BaseOperator):
    name = "raw"
    defaults = {"exclude": None, "ignore": None, "summary": False}
    metrics = (
        ("loc", "Lines of Code", int),
        ("lloc", "L Lines of Code", int),
        ("sloc", "S Lines of Code", int),
        ("comments", "Multi-line comments", int),
        ("multi", "Multi lines", int),
        ("blank", "blank lines", int),
        ("single_comments", "Single comment lines", int)
    )
    
    def __init__(self, config):
        # TODO: Use config from wily.cfg for harvester
        logger.debug(f"Using {config.targets} with {self.defaults} for Raw metrics")
        self.harvester = harvesters.RawHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
