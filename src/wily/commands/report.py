"""
Report command.

The report command gives a table of metrics for a specified list of files.
Will compare the values between revisions and highlight changes in green/red.
"""

import pathlib
from collections.abc import Iterable
from pathlib import Path
from shutil import copytree
from string import Template

from rich.text import Text

from wily import MAX_MESSAGE_WIDTH, format_date, format_revision, logger
from wily.backend import WilyIndex
from wily.cache import list_archivers
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.helper.custom_enums import ReportFormat
from wily.lang import _
from wily.operators import ALL_METRICS, MetricType, resolve_metric_as_tuple

# Rich style names for metric changes
STYLE_RED = "red"
STYLE_GREEN = "green"
STYLE_YELLOW = "yellow"


def report(
    config: WilyConfig,
    path: str,
    metrics: Iterable[str] | None,
    n: int | None,
    output: Path,
    include_message: bool = False,
    format: ReportFormat = ReportFormat.CONSOLE,
    changes_only: bool = False, # ignore in v2
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
    :param changes_only: Only report revisions where delta != 0 (ignored - parquet only stores changes)
    :param wrap: Wrap output
    :param table_style: Table box style
    """
    if metrics is None:
        resolved_metrics = ALL_METRICS
    else:
        metrics = sorted(set(metrics))
        resolved_metrics = [resolve_metric_as_tuple(metric_name) for metric_name in metrics]

    logger.debug("Running report command")

    # Build metric metadata for display styling
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

    archivers = list_archivers(config)

    if not archivers:
        logger.error("No wily cache found. Run 'wily build' first.")
        return

    data: list[tuple[str | Text, ...]] = []

    for archiver in archivers:
        parquet_path = pathlib.Path(config.cache_path) / archiver / "metrics.parquet"
        if not parquet_path.exists():
            logger.debug("No parquet file for archiver %s", archiver)
            continue

        # Use WilyIndex to query data for the path
        operator_names = [meta["operator"] for meta in metric_metas]
        with WilyIndex(str(parquet_path), operator_names) as index:
            # Check if this is a granular query (e.g., "file.py:function_name")
            is_granular = ":" in path

            # Get all rows for this path
            # For granular paths (file.py:function), accept any path_type
            # For file paths, filter to file-level entries only
            if is_granular:
                rows = list(index[path])
            else:
                rows = [row for row in index[path] if row.get("path_type") == "file"]
            # Sort by date (oldest first) and limit to n
            rows = sorted(rows, key=lambda r: r.get("revision_date", 0))[-(n or len(rows)):]

            last: dict = {}
            for row in rows:
                deltas = []
                vals: list[str | Text] = []

                for meta in metric_metas:
                    try:
                        val = row.get(meta["key"])
                        if val is None:
                            k: str | Text = "N/A"
                            delta = 0
                        elif meta["type"] in (int, float):
                            # Ensure val is numeric
                            if not isinstance(val, (int, float)):
                                k = f"{val}"
                                delta = 0
                            else:
                                last_val = last.get(meta["key"])
                                if last_val is not None and isinstance(last_val, (int, float)):
                                    delta = val - last_val
                                else:
                                    delta = 0
                                last[meta["key"]] = val

                                # Build a Rich Text object with styled delta
                                cell = Text(f"{val:n} (")
                                if delta == 0:
                                    cell.append(str(delta))
                                elif delta < 0:
                                    cell.append(f"{delta:n}", style=meta["decrease_style"])
                                else:
                                    cell.append(f"+{delta:n}", style=meta["increase_style"])
                                cell.append(")")
                                k = cell
                        else:
                            k = f"{val}"
                            delta = 0
                    except (KeyError, TypeError) as e:
                        k = f"Not found {e}"
                        delta = 0
                    deltas.append(delta)
                    vals.append(k)

                # Build row data
                revision_key = row.get("revision", "")
                author = row.get("revision_author", "")
                date = row.get("revision_date", 0)
                message = row.get("revision_message", "")

                if include_message:
                    data.append(
                        (
                            format_revision(revision_key),
                            (message or "")[:MAX_MESSAGE_WIDTH],
                            str(author or ""),
                            format_date(date),
                            *vals,
                        )
                    )
                else:
                    data.append(
                        (
                            format_revision(revision_key),
                            str(author or ""),
                            format_date(date),
                            *vals,
                        )
                    )

    if not data:
        logger.error("No data found for %s.", path)
        return

    descriptions = [meta["title"] for meta in metric_metas]
    if include_message:
        headers = (_("Revision"), _("Message"), _("Author"), _("Date"), *descriptions)
    else:
        headers = (_("Revision"), _("Author"), _("Date"), *descriptions)

    if format == ReportFormat.HTML:
        _render_html_report(output, headers, data)
    else:
        print_table(headers=headers, data=data[::-1], wrap=wrap, table_style=table_style)


def _render_html_report(output: Path, headers: tuple, data: list) -> None:
    """Render the report as HTML."""
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
