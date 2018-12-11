# -*- coding: UTF-8 -*-
"""Main command line."""

import os.path

import click

from wily import logger
from wily.archivers import resolve_archiver
from wily.cache import exists, get_default_metrics
from wily.config import DEFAULT_CONFIG_PATH, DEFAULT_CACHE_PATH
from wily.config import load as load_config
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
    """
    \U0001F98A Inspect and search through the complexity of your source code.

    To get started, run setup:

      $ wily setup

    To reindex any changes in your source code:

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
    "-n",
    "--max-revisions",
    default=None,
    type=click.INT,
    help="The maximum number of historical commits to archive",
)
@click.argument("targets", type=click.Path(resolve_path=True), nargs=-1, required=True)
@click.option(
    "-o",
    "--operators",
    type=click.STRING,
    help="List of operators, separated by commas",
)
@click.option(
    "-a",
    "--archiver",
    type=click.STRING,
    default="git",
    help="Archiver to use, defaults to git if git repo, else filesystem",
)
@click.option(
    "--skip-gitignore-check/--gitignore-check",
    default=False,
    help="Skip checking of .gitignore for '.wily/'",
)
@click.pass_context
def build(ctx, max_revisions, targets, operators, skip_gitignore_check, archiver):
    """Build the wily cache."""
    config = ctx.obj["CONFIG"]

    from wily.commands.build import build

    if max_revisions:
        logger.debug(f"Fixing revisions to {max_revisions}")
        config.max_revisions = max_revisions

    if operators:
        logger.debug(f"Fixing operators to {operators}")
        config.operators = operators.strip().split(",")

    if archiver:
        logger.debug(f"Fixing archiver to {archiver}")
        config.archiver = archiver

    config.skip_ignore_check = skip_gitignore_check
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
        handle_no_cache(ctx)

    from wily.commands.index import index

    index(config=config, include_message=message)


@cli.command()
@click.argument("file", type=click.Path(resolve_path=False))
@click.argument("metrics", nargs=-1, required=False)
@click.option("-n", "--number", help="Number of items to show", type=click.INT)
@click.option("--message/--no-message", default=False, help="Include revision message")
@click.pass_context
def report(ctx, file, metrics, number, message):
    """Show metrics for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    if not metrics:
        metrics = get_default_metrics(config)
        logger.info(f"Using default metrics {metrics}")

    from wily.commands.report import report

    logger.debug(f"Running report on {file} for metric {metrics}")
    report(config=config, path=file, metrics=metrics, n=number, include_message=message)


@cli.command()
@click.argument("files", type=click.Path(resolve_path=False), nargs=-1, required=True)
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
        handle_no_cache(ctx)

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
@click.argument("path", type=click.Path(resolve_path=False))
@click.argument("metrics", nargs=-2, required=True)
@click.option(
    "-o", "--output", help="Output report to specified HTML path, e.g. reports/out.html"
)
@click.option("-x", "--x-axis", help="Metric to use on x-axis, defaults to history.")
@click.option(
    "-a/-c", "--changes/--all", default=True, help="All commits or changes only"
)
@click.pass_context
def graph(ctx, path, metrics, output, x_axis, changes):
    """
    Graph a specific metric for a given file, if a path is given, all files within path will be graphed.

    Some common examples:

    Graph all .py files within src/ for the raw.loc metric

        $ wily graph src/ raw.loc

    Graph test.py against raw.loc and cyclomatic.complexity metrics

        $ wily graph src/test.py raw.loc cyclomatic.complexity

    Graph test.py against raw.loc and raw.sloc on the x-axis

        $ wily graph src/test.py raw.loc --x-axis raw.sloc
    """
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    from wily.commands.graph import graph

    logger.debug(f"Running report on {path} for metrics {metrics}")
    graph(
        config=config,
        path=path,
        metrics=metrics,
        output=output,
        x_axis=x_axis,
        changes=changes,
    )


@cli.command()
@click.option("-y/-p", "--yes/--prompt", default=False, help="Skip prompt")
@click.pass_context
def clean(ctx, yes):
    """Clear the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    if not yes:
        p = input("Are you sure you want to delete wily cache? [y/N]")
        if p.lower() != "y":
            exit(0)

    from wily.cache import clean

    clean(config)


@cli.command("list-metrics")
@click.pass_context
def list_metrics(ctx):
    """List the available metrics."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    from wily.commands.list_metrics import list_metrics

    list_metrics()


@cli.command("setup")
@click.pass_context
def setup(ctx):
    """Run a guided setup to build the wily cache."""
    handle_no_cache(ctx)


def handle_no_cache(context):
    """Handle lack-of-cache error, prompt user for index process."""
    logger.error(
        f"Could not locate wily cache, the cache is required to provide insights."
    )
    p = input("Do you want to run setup and index your project now? [y/N]")
    if p.lower() != "y":
        exit(1)
    else:
        revisions = input("How many previous git revisions do you want to index? : ")
        revisions = int(revisions)
        path = input("Path to your source files; comma-separated for multiple: ")
        paths = path.split(",")
        context.invoke(
            build,
            max_revisions=revisions,
            targets=paths,
            operators=None,
            skip_gitignore_check=False,
        )


if __name__ == "__main__":
    cli()  # pragma: no cover
