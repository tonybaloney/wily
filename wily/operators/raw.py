import radon.cli.harvest as harvesters
from radon.cli import Config
from wily import logger
from wily.operators import BaseOperator, MetricType, Metric


class RawMetricsOperator(BaseOperator):
    name = "raw"
    defaults = {"exclude": None, "ignore": None, "summary": False}
    metrics = (
        Metric("loc", "Lines of Code", int, MetricType.Informational),
        Metric("lloc", "L Lines of Code", int, MetricType.AimLow),
        Metric("sloc", "S Lines of Code", int, MetricType.AimLow),
        Metric("comments", "Multi-line comments", int, MetricType.AimHigh),
        Metric("multi", "Multi lines", int, MetricType.Informational),
        Metric("blank", "blank lines", int, MetricType.Informational),
        Metric(
            "single_comments", "Single comment lines", int, MetricType.Informational
        ),
    )
    default_metric_index = 0  # LOC

    def __init__(self, config):
        # TODO: Use config from wily.cfg for harvester
        logger.debug(f"Using {config.targets} with {self.defaults} for Raw metrics")
        self.harvester = harvesters.RawHarvester(
            config.targets, config=Config(**self.defaults)
        )

    def run(self, module, options):
        logger.debug("Running raw harvester")
        return dict(self.harvester.results)
