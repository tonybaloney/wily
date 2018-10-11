import click
from .config import load as load_config


@click.group(name="history")
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def history_cli(ctx, debug):
    """Commands for creating and searching through history"""
    ctx.ensure_object(dict)

    ctx.obj['DEBUG'] = debug

    ctx.obj['CONFIG'] = load_config()


@history_cli.command()
@click.option("--max-history", default=100, help="The maximum number of historical commits to try")
@click.pass_context
def build():
    """Build the complexity history log based on a version-control system"""
    pass


@history_cli.command()
def show():
    """Show the history archive in the .wily/ folder"""
    pass


@click.group(invoke_without_command=True)
def run_cli():
    pass


cli = click.CommandCollection(sources=[history_cli, run_cli])

if __name__ == '__main__':
    cli()
