import click
from wily import logger
from wily.cache import exists
from wily.config import load as load_config
from wily.config import DEFAULT_CONFIG_PATH
from wily.archivers import resolve_archiver
from wily.operators import resolve_operators


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
    help="The maximum number of historical commits to try",
)
@click.option("-p", "--path", type=click.Path(resolve_path=True))
@click.pass_context
def build(ctx, max_revisions, path):
    """Build the complexity history log based on a version-control system"""
    config = ctx.obj["CONFIG"]

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
    logger.info(
        "Completed building wily history, run `wily graph` or `wily show` to see more."
    )


@cli.command()
@click.pass_context
def show(ctx):
    """Show the history archive in the .wily/ folder"""
    config = ctx.obj["CONFIG"]

    if not exists():
        logger.error(f"Could not locate wily cache. Run `wily build` first.")

    from wily.commands.show import show

    show(config=config)


cli()
