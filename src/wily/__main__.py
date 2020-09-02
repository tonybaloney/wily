# -*- coding: UTF-8 -*-
"""Main command line."""

import click
import traceback
from pathlib import Path

from wily import logger, __version__, WILY_LOG_NAME
from wily.archivers import resolve_archiver
from wily.cache import exists, get_default_metrics
from wily.config import DEFAULT_CONFIG_PATH, DEFAULT_GRID_STYLE
from wily.config import load as load_config
from wily.helper.custom_enums import ReportFormat
from wily.operators import resolve_operators
from wily.lang import _

version_text = _("Version: ") + __version__ + "\n\n"
help_header = version_text + _(
"""\U0001F98A Inspect and search through the complexity of your source code.
To get started, run setup:

  $ wily setup
  
To reindex any changes in your source code:

  $ wily build <src>
  
Then explore basic metrics with:

  $ wily report <file>
  
You can also graph specific metrics in a browser with:

  $ wily graph <file> <metric>
  
""")

@click.group(help=help_header)
@click.version_option(
    __version__, "-V", "--version", message="\U0001F98A %(prog)s, {version} %(version)s".format(version=_("version")),
    help=_("Show the version and exit.")
)
@click.help_option(help=_("Show this message and exit."))
@click.option(
    "--debug/--no-debug",
    default=False,
    help=_("Print debug information, used for development"),
)
@click.option(
    "--config",
    default=DEFAULT_CONFIG_PATH,
    help=_("Path to configuration file, defaults to wily.cfg"),
)
@click.option(
    "-p",
    "--path",
    type=click.Path(resolve_path=True),
    default=".",
    help=_("Root path to the project folder to scan"),
)
@click.option(
    "-c",
    "--cache",
    type=click.Path(resolve_path=True),
    help=_("Override the default cache path (defaults to $HOME/.wily/HASH)"),
)
@click.pass_context
def cli(ctx, debug, config, path, cache):
    """CLI entry point."""
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
    if cache:
        logger.debug(f"Fixing cache to {cache}")
        ctx.obj["CONFIG"].cache_path = cache
    logger.debug(f"Loaded configuration from {config}")
    logger.debug(f"Capturing logs to {WILY_LOG_NAME}")


@cli.command(help=_("""Build the wily cache."""))
@click.option(
    "-n",
    "--max-revisions",
    default=None,
    type=click.INT,
    help=_("The maximum number of historical commits to archive"),
)
@click.argument("targets", type=click.Path(resolve_path=True), nargs=-1, required=False)
@click.option(
    "-o",
    "--operators",
    type=click.STRING,
    help=_("List of operators, separated by commas"),
)
@click.option(
    "-a",
    "--archiver",
    type=click.STRING,
    default="git",
    help=_("Archiver to use, defaults to git if git repo, else filesystem"),
)
@click.pass_context
def build(ctx, max_revisions, targets, operators, archiver):
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

    if targets:
        logger.debug(f"Fixing targets to {targets}")
        config.targets = targets

    build(
        config=config,
        archiver=resolve_archiver(config.archiver),
        operators=resolve_operators(config.operators),
    )
    logger.info(
        _("Completed building wily history, run `wily report <file>` or `wily index` to see more.")
    )


@cli.command(help=_("""Show the history archive in the .wily/ folder."""))
@click.pass_context
@click.option(
    "-m", "--message/--no-message", default=False, help=_("Include revision message")
)
def index(ctx, message):
    """Show the history archive in the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    from wily.commands.index import index

    index(config=config, include_message=message)


@cli.command(help = _("""
    Rank files, methods and functions in order of any metrics, e.g. complexity.

    Some common examples:

    Rank all .py files within src/ for the maintainability.mi metric

        $ wily rank src/ maintainability.mi

    Rank all .py files in the index for the default metrics across all archivers

        $ wily rank

    Rank all .py files in the index for the default metrics across all archivers
    and return a non-zero exit code if the total is below the given threshold

        $ wily rank --threshold=80
    """))
@click.argument("path", type=click.Path(resolve_path=False), required=False)
@click.argument("metric", required=False, default="maintainability.mi")
@click.option(
    "-r", "--revision", help=_("Compare against specific revision"), type=click.STRING
)
@click.option("-l", "--limit", help=_("Limit the number of results shown"), type=click.INT)
@click.option(
    "--desc/--asc",
    help=_("Order to show results (ascending or descending)"),
    default=False,
)
@click.option(
    "--threshold",
    help=_("Return a non-zero exit code under the specified threshold"),
    type=click.INT,
)
@click.pass_context
def rank(ctx, path, metric, revision, limit, desc, threshold):
    """Rank files, methods and functions in order of any metrics, e.g. complexity."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    from wily.commands.rank import rank

    logger.debug(f"Running rank on {path} for metric {metric} and revision {revision}")
    rank(
        config=config,
        path=path,
        metric=metric,
        revision_index=revision,
        limit=limit,
        threshold=threshold,
        descending=desc,
    )


@cli.command(help=_("""Show metrics for a given file."""))
@click.argument("file", type=click.Path(resolve_path=False))
@click.argument("metrics", nargs=-1, required=False)
@click.option("-n", "--number", help="Number of items to show", type=click.INT)
@click.option(
    "-m", "--message/--no-message", default=False, help=_("Include revision message")
)
@click.option(
    "-f",
    "--format",
    default=ReportFormat.CONSOLE.name,
    help=_("Specify report format (console or html)"),
    type=click.Choice(ReportFormat.get_all()),
)
@click.option(
    "--console-format",
    default=DEFAULT_GRID_STYLE,
    help=_("Style for the console grid, see Tabulate Documentation for a list of styles."),
)
@click.option(
    "-o", "--output", help=_("Output report to specified HTML path, e.g. reports/out.html")
)
@click.pass_context
def report(ctx, file, metrics, number, message, format, console_format, output):
    """Show metrics for a given file."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    if not metrics:
        metrics = get_default_metrics(config)
        logger.info(f"Using default metrics {metrics}")

    new_output = Path().cwd()
    if output:
        new_output = new_output / Path(output)
    else:
        new_output = new_output / "wily_report" / "index.html"

    from wily.commands.report import report

    logger.debug(f"Running report on {file} for metric {metrics}")
    logger.debug(f"Output format is {format}")

    report(
        config=config,
        path=file,
        metrics=metrics,
        n=number,
        output=new_output,
        include_message=message,
        format=ReportFormat[format],
        console_format=console_format,
    )


@cli.command(help=_("""Show the differences in metrics for each file."""))
@click.argument("files", type=click.Path(resolve_path=False), nargs=-1, required=True)
@click.option(
    "-m",
    "--metrics",
    default=None,
    help=_("comma-seperated list of metrics, see list-metrics for choices"),
)
@click.option(
    "-a/-c",
    "--all/--changes-only",
    default=False,
    help=_("Show all files, instead of changes only"),
)
@click.option(
    "--detail/--no-detail",
    default=True,
    help=_("Show function/class level metrics where available"),
)
@click.option(
    "-r", "--revision", help=_("Compare against specific revision"), type=click.STRING
)
@click.pass_context
def diff(ctx, files, metrics, all, detail, revision):
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
        config=config,
        files=files,
        metrics=metrics,
        changes_only=not all,
        detail=detail,
        revision=revision,
    )


@cli.command(help=_("""
    Graph a specific metric for a given file, if a path is given, all files within path will be graphed.

    Some common examples:

    Graph all .py files within src/ for the raw.loc metric

        $ wily graph src/ raw.loc

    Graph test.py against raw.loc and cyclomatic.complexity metrics

        $ wily graph src/test.py raw.loc cyclomatic.complexity

    Graph test.py against raw.loc and raw.sloc on the x-axis

        $ wily graph src/test.py raw.loc --x-axis raw.sloc
    """))
@click.argument("path", type=click.Path(resolve_path=False))
@click.argument("metrics", nargs=-2, required=True)
@click.option(
    "-o", "--output", help=_("Output report to specified HTML path, e.g. reports/out.html")
)
@click.option("-x", "--x-axis", help=_("Metric to use on x-axis, defaults to history."))
@click.option(
    "-a/-c", "--changes/--all", default=True, help=_("All commits or changes only")
)
@click.pass_context
def graph(ctx, path, metrics, output, x_axis, changes):
    """Output report to specified HTML path, e.g. reports/out.html."""
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


@cli.command(help=_("""Clear the .wily/ folder."""))
@click.option("-y/-p", "--yes/--prompt", default=False, help=_("Skip prompt"))
@click.pass_context
def clean(ctx, yes):
    """Clear the .wily/ folder."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        logger.info(_("Wily cache does not exist, nothing to remove."))
        exit(0)

    if not yes:
        p = input(_("Are you sure you want to delete wily cache? [y/N]"))
        if p.lower() != "y":
            exit(0)

    from wily.cache import clean

    clean(config)


@cli.command("list-metrics", help=_("""List the available metrics."""))
@click.pass_context
def list_metrics(ctx):
    """List the available metrics."""
    config = ctx.obj["CONFIG"]

    if not exists(config):
        handle_no_cache(ctx)

    from wily.commands.list_metrics import list_metrics

    list_metrics()


@cli.command("setup", help=_("""Run a guided setup to build the wily cache."""))
@click.pass_context
def setup(ctx):
    """Run a guided setup to build the wily cache."""
    handle_no_cache(ctx)


def handle_no_cache(context):
    """Handle lack-of-cache error, prompt user for index process."""
    logger.error(
        _("Could not locate wily cache, the cache is required to provide insights.")
    )
    p = input(_("Do you want to run setup and index your project now? [y/N]"))
    if p.lower() != "y":
        exit(1)
    else:
        revisions = input(_("How many previous git revisions do you want to index? : "))
        revisions = int(revisions)
        path = input(_("Path to your source files; comma-separated for multiple: "))
        paths = path.split(",")
        context.invoke(build, max_revisions=revisions, targets=paths, operators=None)


if __name__ == "__main__":  # pragma: no cover
    try:
        cli()
    except Exception as runtime:
        logger.error(f"Oh no, Wily crashed! See {WILY_LOG_NAME} for information.")
        logger.info(
            f"If you think this crash was unexpected, please raise an issue at https://github.com/tonybaloney/wily/issues and copy the log file into the issue report along with some information on what you were doing."
        )
        logger.debug(traceback.format_exc())
