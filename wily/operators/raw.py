import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator, MetricType


class RawMetricsOperator(BaseOperator):
    name = "raw"
    defaults = {"exclude": None, "ignore": None, "summary": False}
    metrics = (
        ("loc", "Lines of Code", int, MetricType.Informational),
        ("lloc", "L Lines of Code", int, MetricType.Informational),
        ("sloc", "S Lines of Code", int, MetricType.Informational),
        ("comments", "Multi-line comments", int, MetricType.Informational),
        ("multi", "Multi lines", int, MetricType.Informational),
        ("blank", "blank lines", int, MetricType.Informational),
        ("single_comments", "Single comment lines", int, MetricType.Informational)
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
