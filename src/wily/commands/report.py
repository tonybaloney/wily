"""
Report command.

The report command gives a table of metrics for a specified list of files.
Will compare the values between revisions and highlight changes in green/red.
"""

from collections.abc import Iterable
from pathlib import Path
from shutil import copytree
from string import Template

from rich.text import Text

from wily import MAX_MESSAGE_WIDTH, format_date, format_revision, logger
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.helper.custom_enums import ReportFormat
from wily.lang import _
from wily.operators import ALL_METRICS, MetricType, resolve_metric_as_tuple
from wily.state import State

# Rich style names for metric changes
STYLE_RED = "red"
STYLE_GREEN = "green"
STYLE_YELLOW = "yellow"


def report(  # noqa: C901, PLR0915
    config: WilyConfig,
    path: str,
    metrics: Iterable[str] | None,
    n: int,
    output: Path,
    include_message: bool = False,
    format: ReportFormat = ReportFormat.CONSOLE,
    changes_only: bool = False,
    wrap: bool = False,
    table_style: str = DEFAULT_TABLE_STYLE,
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
    :param changes_only: Only report revisions where delta != 0
    :param wrap: Wrap output
    :param table_style: Table box style
    """
    if metrics is None:
        resolved_metrics = ALL_METRICS
    else:
        metrics = sorted(set(metrics))
        resolved_metrics = [resolve_metric_as_tuple(metric_name) for metric_name in metrics]

    logger.debug("Running report command")

    data: list[tuple[str | Text, ...]] = []
    metric_metas = []

    for operator, metric in resolved_metrics:
        key = metric.name
        # Set the delta styles depending on the metric type
        if metric.measure == MetricType.AimHigh:
            increase_style = STYLE_GREEN
            decrease_style = STYLE_RED
        elif metric.measure == MetricType.AimLow:
            increase_style = STYLE_RED
            decrease_style = STYLE_GREEN
        elif metric.measure == MetricType.Informational:
            increase_style = STYLE_YELLOW
            decrease_style = STYLE_YELLOW
        else:
            increase_style = STYLE_YELLOW
            decrease_style = STYLE_YELLOW
        metric_meta = {
            "key": key,
            "operator": operator.name,
            "increase_style": increase_style,
            "decrease_style": decrease_style,
            "title": metric.description,
            "type": metric.metric_type,
        }
        metric_metas.append(metric_meta)

    state = State(config)
    for archiver in state.archivers:
        history = state.index[archiver].revisions[:n][::-1]
        last: dict = {}
        for rev in history:
            deltas = []
            vals: list[str | Text] = []
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

                    if meta["type"] in (int, float):
                        # Build a Rich Text object with styled delta
                        cell = Text(f"{val:n} (")
                        if delta == 0:
                            cell.append(str(delta))
                        elif delta < 0:
                            cell.append(f"{delta:n}", style=meta["decrease_style"])
                        else:
                            cell.append(f"+{delta:n}", style=meta["increase_style"])
                        cell.append(")")
                        k: str | Text = cell
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

        # Style to HTML class mapping
        style_to_html = {
            "green": "green-color",
            "red": "red-color",
            "yellow": "orange-color",
        }

        def text_to_html(text_obj: Text) -> str:
            """Convert a Rich Text object to HTML."""
            result = ""
            plain = text_obj.plain
            # If no styles, just return plain text
            if not text_obj._spans:  # noqa: SLF001
                return plain
            # Build HTML from spans
            last_end = 0
            for start, end, style in text_obj._spans:  # noqa: SLF001
                # Add unstyled text before this span
                if start > last_end:
                    result += plain[last_end:start]
                # Add styled text
                span_text = plain[start:end]
                if style:
                    html_class = style_to_html.get(str(style), "")
                    if html_class:
                        result += f"<span class='{html_class}'>{span_text}</span>"
                    else:
                        result += span_text
                else:
                    result += span_text
                last_end = end
            # Add any remaining unstyled text
            if last_end < len(plain):
                result += plain[last_end:]
            return result

        table_headers = "".join([f"<th>{header}</th>" for header in headers])
        table_content = ""
        for line in data[::-1]:
            table_content += "<tr>"
            for element in line:
                if isinstance(element, Text):
                    table_content += f"<td>{text_to_html(element)}</td>"
                else:
                    table_content += f"<td>{element}</td>"
            table_content += "</tr>"

        rendered_report = report_template.safe_substitute(headers=table_headers, content=table_content)

        with report_output.open("w", errors="xmlcharrefreplace") as output_f:
            output_f.write(rendered_report)

        try:
            copytree(str(templates_dir / "css"), str(report_path / "css"))
        except FileExistsError:
            pass

        logger.info("wily report was saved to %s", report_path)
    else:
        print_table(headers=headers, data=data[::-1], wrap=wrap, table_style=table_style)
