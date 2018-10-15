import click
from wily import logger
from wily.cache import exists
from wily.config import load as load_config
from wily.config import DEFAULT_CONFIG_PATH
from wily.archivers import resolve_archiver
from wily.operators import resolve_operators


@click.group()
@click.option("--debug/--no-debug", default=False, help="Print debug information, used for development")
@click.option(
    "--config",
    default=DEFAULT_CONFIG_PATH,
    help="Path to configuration file, defaults to wily.cfg",
)
@click.pass_context
def cli(ctx, debug, config):
    """Commands for creating and searching through history."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    if debug:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")
    ctx.obj["CONFIG"] = load_config(config)
    logger.debug(f"Loaded configuration from {config}")


@cli.command()
@click.option(
    "-h",
    "--max-revisions",
    default=None,
    type=click.INT,
    help="The maximum number of historical commits to archive",
)
@click.option("-p", "--path", type=click.Path(resolve_path=True),
    help="Root path to the project folder to scan")
@click.option(
    "-t",
    "--target",
    default=None,
    type=click.Path(resolve_path=True),
    multiple=True,
    help="Subdirectories or files to scan",
)
@click.option("-o", "--operators", type=click.STRING, help="List of operators, seperated by commas")
@click.pass_context
def build(ctx, max_revisions, path, target, operators):
    """Build the wily cache"""
    config = ctx.obj["CONFIG"]

    from wily.commands.build import build

    if max_revisions:
        logger.debug(f"Fixing revisions to {max_revisions}")
        config.max_revisions = max_revisions
    if path:
        logger.debug(f"Fixing path to {path}")
        config.path = path
    if target:
        logger.debug(f"Fixing targets to {target}")
        config.targets = target
    if operators:
        logger.debug(f"Fixing operators to {operators}")
        config.operators = operators.split(',')

    build(
        config=config,
        archiver=resolve_archiver(config.archiver),
        operators=resolve_operators(config.operators),
    )
    logger.info(
        "Completed building wily history, run `wily report` or `wily show` to see more."
    )


@cli.command()
@click.pass_context
def index(ctx):
    """Show the history archive in the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache. Run `wily build` first.")
        return -1

    from wily.commands.index import index

    index(config=config)


@cli.command()
@click.argument("file", type=click.Path(resolve_path=False))
@click.argument("metric")
@click.pass_context
def report(ctx, file, metric):
    """Show a specific metric for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache. Run `wily build` first.")
        return -1

    from wily.commands.report import report
    logger.debug(f"Running report on {file} for metric {metric}")
    report(config=config, path=file, metric=metric)


@cli.command()
@click.argument("file", type=click.Path(resolve_path=False))
@click.argument("metric")
@click.pass_context
def graph(ctx, file, metric):
    """Graph a specific metric for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache. Run `wily build` first.")
        return -1

    from wily.commands.graph import graph
    logger.debug(f"Running report on {file} for metric {metric}")
    graph(config=config, path=file, metric=metric)


@cli.command()
@click.option("-y", "--yes", default=False, help="Skip prompt")
@click.pass_context
def clean(ctx, yes):
    """Clear the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache.")
        return 0

    if not yes:
        p = input("Are you sure you want to delete wily cache? [y/N]")
        if p.lower() != 'y':
            return 0

    from wily.cache import clean

    clean()


@cli.command("list-metrics")
@click.pass_context
def list_metrics(ctx):
    """List the available metrics"""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache.")
        return -1

    from wily.commands.list_metrics import list_metrics

    list_metrics()

cli()
