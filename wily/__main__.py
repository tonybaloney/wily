# -*- coding: UTF-8 -*-

"""
Main command line

TODO : Skip-ignore-check should be a flag not a value option

"""

import os.path
import click
from wily import logger
from wily.cache import exists, get_default_metrics
from wily.config import load as load_config
from wily.config import DEFAULT_CONFIG_PATH, DEFAULT_CACHE_PATH
from wily.archivers import resolve_archiver
from wily.operators import resolve_operators


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Print debug information, used for development",
)
@click.option(
    "--config",
    default=DEFAULT_CONFIG_PATH,
    help="Path to configuration file, defaults to wily.cfg",
)
@click.option(
    "-p",
    "--path",
    type=click.Path(resolve_path=True),
    default=".",
    help="Root path to the project folder to scan",
)
@click.pass_context
def cli(ctx, debug, config, path):
    """\U0001F98A Inspect and search through the complexity of your source code.

    To get started, build an index of your source code:

      $ wily build <src>

    Then explore basic metrics with:

      $ wily report <file>

    You can also graph specific metrics in a browser with:

      $ wily graph <file> <metric>
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    ctx.obj["CONFIG"] = load_config(config)
    if path:
        logger.debug(f"Fixing path to {path}")
        ctx.obj["CONFIG"].path = path
        ctx.obj["CONFIG"].cache_path = os.path.join(path, DEFAULT_CACHE_PATH)
    logger.debug(f"Loaded configuration from {config}")


@cli.command()
@click.option(
    "-h",
    "--max-revisions",
    default=None,
    type=click.INT,
    help="The maximum number of historical commits to archive",
)
@click.argument("targets", type=click.Path(resolve_path=True), nargs=-1)
@click.option(
    "-o",
    "--operators",
    type=click.STRING,
    help="List of operators, separated by commas",
)
@click.option(
    "--skip-ignore-check",
    type=click.BOOL,
    default=False,
    help="Skip checking of .gitignore for '.wily/'",
)
@click.pass_context
def build(ctx, max_revisions, targets, operators, skip_ignore_check):
    """Build the wily cache"""
    config = ctx.obj["CONFIG"]

    from wily.commands.build import build

    if max_revisions:
        logger.debug(f"Fixing revisions to {max_revisions}")
        config.max_revisions = max_revisions

    if operators:
        logger.debug(f"Fixing operators to {operators}")
        config.operators = operators.strip().split(",")

    config.skip_ignore_check = skip_ignore_check
    logger.debug(f"Fixing targets to {targets}")
    config.targets = targets

    build(
        config=config,
        archiver=resolve_archiver(config.archiver),
        operators=resolve_operators(config.operators),
    )
    logger.info(
        "Completed building wily history, run `wily report <file>` or `wily index` to see more."
    )


@cli.command()
@click.pass_context
@click.option("--message/--no-message", default=False, help="Include revision message")
def index(ctx, message):
    """Show the history archive in the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache. Run `wily build` first.")
        exit(1)

    from wily.commands.index import index

    index(config=config, include_message=message)


@cli.command()
@click.argument("file", type=click.Path(resolve_path=False))
@click.option(
    "--metrics",
    default=None,
    help="comma-seperated list of metrics, see list-metrics for choices",
)
@click.option("-n", "--number", help="Number of items to show", type=click.INT)
@click.option("--message/--no-message", default=False, help="Include revision message")
@click.pass_context
def report(ctx, file, metrics, number, message):
    """Show metrics for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache. Run `wily build <target>` first.")
        exit(1)

    if not metrics:
        metrics = get_default_metrics(config)
        logger.info(f"Using default metrics {metrics}")
    else:
        metrics = metrics.split(",")

    from wily.commands.report import report

    logger.debug(f"Running report on {file} for metric {metrics}")
    report(config=config, path=file, metrics=metrics, n=number, include_message=message)


@cli.command()
@click.argument("files", type=click.Path(resolve_path=False), nargs=-1)
@click.option(
    "--metrics",
    default=None,
    help="comma-seperated list of metrics, see list-metrics for choices",
)
@click.option(
    "--all/--changes-only",
    default=False,
    help="Show all files, instead of changes only",
)
@click.option(
    "--detail/--no-detail",
    default=True,
    help="Show function/class level metrics where available",
)
@click.pass_context
def diff(ctx, files, metrics, all, detail):
    """Show the differences in metrics for each file."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache. Run `wily build <target>` first.")
        exit(1)

    if not metrics:
        metrics = get_default_metrics(config)
        logger.info(f"Using default metrics {metrics}")
    else:
        metrics = metrics.split(",")
        logger.info(f"Using specified metrics {metrics}")

    from wily.commands.diff import diff

    logger.debug(f"Running diff on {files} for metric {metrics}")
    diff(
        config=config, files=files, metrics=metrics, changes_only=not all, detail=detail
    )


@cli.command()
@click.argument("files", type=click.Path(resolve_path=False))
@click.argument("metrics", nargs=-1)
@click.option(
    "-o", "--output", help="Output report to specified HTML path, e.g. reports/out.html"
)
@click.pass_context
def graph(ctx, files, metrics, output):
    """Graph a specific metric for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache. Run `wily build <target>` first.")
        exit(1)

    from wily.commands.graph import graph

    logger.debug(f"Running report on {files} for metrics {metrics}")
    graph(config=config, paths=[files], metrics=metrics, output=output)


@cli.command()
@click.option("-y/-p", "--yes/--prompt", default=False, help="Skip prompt")
@click.pass_context
def clean(ctx, yes):
    """Clear the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache.")
        exit(1)

    if not yes:
        p = input("Are you sure you want to delete wily cache? [y/N]")
        if p.lower() != "y":
            exit(0)

    from wily.cache import clean

    clean(config)


@cli.command("list-metrics")
@click.pass_context
def list_metrics(ctx):
    """List the available metrics"""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.error(f"Could not locate wily cache.")
        exit(1)

    from wily.commands.list_metrics import list_metrics

    list_metrics()


if __name__ == "__main__":
    cli()
