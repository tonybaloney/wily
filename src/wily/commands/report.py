"""
Report command.

The report command gives a table of metrics for a specified list of files.
Will compare the values between revisions and highlight changes in green/red.
"""
from pathlib import Path
from shutil import copytree
from string import Template
from typing import Dict, Iterable, List, Tuple

import tabulate

from wily import MAX_MESSAGE_WIDTH, format_date, format_revision, logger
from wily.config.types import WilyConfig
from wily.helper import get_maxcolwidth
from wily.helper.custom_enums import ReportFormat
from wily.lang import _
from wily.operators import MetricType, resolve_metric_as_tuple
from wily.state import State

ANSI_RED = 31
ANSI_GREEN = 32
ANSI_YELLOW = 33


def report(
    config: WilyConfig,
    path: str,
    metrics: Iterable[str],
    n: int,
    output: Path,
    console_format: str,
    include_message: bool = False,
    format: ReportFormat = ReportFormat.CONSOLE,
    changes_only: bool = False,
    wrap: bool = False,
) -> None:
    """
    Show metrics for a given file.

    :param config: The configuration
    :param path: The path to the file
    :param metrics: List of metrics to report on
    :param n: Number of items to list
    :param output: Output path
    :param include_message: Include revision messages
    :param format: Output format
    :param console_format: Grid format style for tabulate
    :param changes_only: Only report revisions where delta != 0
    :param wrap: Wrap output
    """
    metrics = sorted(metrics)
    logger.debug("Running report command")
    logger.info("-----------History for %s------------", metrics)

    data: List[Tuple[str, ...]] = []
    metric_metas = []

    for metric_name in metrics:
        operator, metric = resolve_metric_as_tuple(metric_name)
        key = metric.name
        # Set the delta colors depending on the metric type
        if metric.measure == MetricType.AimHigh:
            increase_color = ANSI_GREEN
            decrease_color = ANSI_RED
        elif metric.measure == MetricType.AimLow:
            increase_color = ANSI_RED
            decrease_color = ANSI_GREEN
        elif metric.measure == MetricType.Informational:
            increase_color = ANSI_YELLOW
            decrease_color = ANSI_YELLOW
        else:
            increase_color = ANSI_YELLOW
            decrease_color = ANSI_YELLOW
        metric_meta = {
            "key": key,
            "operator": operator.name,
            "increase_color": increase_color,
            "decrease_color": decrease_color,
            "title": metric.description,
            "type": metric.metric_type,
        }
        metric_metas.append(metric_meta)

    state = State(config)
    for archiver in state.archivers:
        history = state.index[archiver].revisions[:n][::-1]
        last: Dict = {}
        for rev in history:
            deltas = []
            vals = []
            for meta in metric_metas:
                try:
                    logger.debug(
                        "Fetching metric %s for %s in %s",
                        meta["key"],
                        meta["operator"],
                        path,
                    )
                    val = rev.get(config, archiver, meta["operator"], path, meta["key"])

                    last_val = last.get(meta["key"], None)
                    # Measure the difference between this value and the last
                    if meta["type"] in (int, float):
                        if last_val:
                            delta = val - last_val
                        else:
                            delta = 0
                        last[meta["key"]] = val
                    else:
                        # TODO : Measure ranking increases/decreases for str types?
                        delta = 0

                    if delta == 0:
                        delta_col = delta
                    elif delta < 0:
                        delta_col = (
                            f"\u001b[{meta['decrease_color']}m{delta:n}\u001b[0m"
                        )
                    else:
                        delta_col = (
                            f"\u001b[{meta['increase_color']}m+{delta:n}\u001b[0m"
                        )

                    if meta["type"] in (int, float):
                        k = f"{val:n} ({delta_col})"
                    else:
                        k = f"{val}"
                except KeyError as e:
                    k = f"Not found {e}"
                    delta = 0
                deltas.append(delta)
                vals.append(k)
            if not changes_only or any(deltas):
                if include_message:
                    data.append(
                        (
                            format_revision(rev.revision.key),
                            rev.revision.message[:MAX_MESSAGE_WIDTH],
                            str(rev.revision.author_name),
                            format_date(rev.revision.date),
                            *vals,
                        )
                    )
                else:
                    data.append(
                        (
                            format_revision(rev.revision.key),
                            str(rev.revision.author_name),
                            format_date(rev.revision.date),
                            *vals,
                        )
                    )
    if not data:
        logger.error("No data found for %s with changes=%s.", path, changes_only)
        return

    descriptions = [meta["title"] for meta in metric_metas]
    if include_message:
        headers = (_("Revision"), _("Message"), _("Author"), _("Date"), *descriptions)
    else:
        headers = (_("Revision"), _("Author"), _("Date"), *descriptions)

    if format == ReportFormat.HTML:
        if output.suffix == ".html":
            report_path = output.parents[0]
            report_output = output
        else:
            report_path = output
            report_output = output.joinpath("index.html")

        report_path.mkdir(exist_ok=True, parents=True)

        templates_dir = (Path(__file__).parents[1] / "templates").resolve()
        report_template = Template((templates_dir / "report_template.html").read_text())

        table_headers = "".join([f"<th>{header}</th>" for header in headers])
        table_content = ""
        for line in data[::-1]:
            table_content += "<tr>"
            for element in line:
                element = element.replace("\u001b[32m", "<span class='green-color'>")
                element = element.replace("\u001b[31m", "<span class='red-color'>")
                element = element.replace("\u001b[33m", "<span class='orange-color'>")
                element = element.replace("\u001b[0m", "</span>")
                table_content += f"<td>{element}</td>"
            table_content += "</tr>"

        rendered_report = report_template.safe_substitute(
            headers=table_headers, content=table_content
        )

        with report_output.open("w", errors="xmlcharrefreplace") as output_f:
            output_f.write(rendered_report)

        try:
            copytree(str(templates_dir / "css"), str(report_path / "css"))
        except FileExistsError:
            pass

        logger.info("wily report was saved to %s", report_path)
    else:
        maxcolwidth = get_maxcolwidth(headers, wrap)
        print(
            tabulate.tabulate(
                headers=headers,
                tabular_data=data[::-1],
                tablefmt=console_format,
                maxcolwidths=maxcolwidth,
                maxheadercolwidths=maxcolwidth,
            )
        )
