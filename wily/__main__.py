import click
import logging
from wily.config import load as load_config
from wily.config import DEFAULT_CONFIG_PATH, DEFAULT_MAX_REVISIONS
from wily.archivers import resolve_archiver
from wily.operators import resolve_operators

logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.option(
    "--config",
    default=DEFAULT_CONFIG_PATH,
    help="Path to configuration file, defaults to wily.cfg",
)
@click.pass_context
def cli(ctx, debug, config):
    """Commands for creating and searching through history"""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    if debug:
        logger.setLevel(logging.DEBUG)
    ctx.obj["CONFIG"] = load_config(config)
    logging.debug(f"Loaded configuration from {config}")


@cli.command()
@click.option(
    "-h",
    "--max-revisions",
    default=None,
    help="The maximum number of historical commits to try",
)
@click.option(
    "-p",
    "--path",
    type=click.Path(resolve_path=True)
)
@click.pass_context
def build(ctx, max_revisions, path):
    """Build the complexity history log based on a version-control system"""
    config = ctx.obj["CONFIG"]

    logging.debug("Running build command")
    from wily.commands.build import build

    if max_revisions:
        config.max_revisions = max_revisions
    if path:
        config.path = path

    build(
        config=config,
        archiver=resolve_archiver(config.archiver),
        operators=resolve_operators(config.operators),
    )


@cli.command()
@click.pass_context
def show(ctx):
    """Show the history archive in the .wily/ folder"""
    config = ctx.obj["CONFIG"]
    logging.debug("Running show command")


cli()
