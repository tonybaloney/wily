"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""

import json as json_module
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.text import Text

from wily import logger
from wily.backend import WilyIndex, iter_filenames
from wily.cache import get_default_metrics_path
from wily.config import DEFAULT_PATH
from wily.config.types import WilyConfig
from wily.defaults import DEFAULT_ARCHIVER, DEFAULT_TABLE_STYLE
from wily.helper import print_table
from wily.operators import (
    ALL_METRICS,
    ALL_OPERATORS,
    BAD_STYLES,
    GOOD_STYLES,
    Metric,
    Operator,
    OperatorLevel,
    resolve_metric,
    resolve_operator,
)


@dataclass
class MetricDiff:
    """Represents the diff of a single metric."""

    name: str
    before: Any
    after: Any
    metric: Metric
    changed: bool = field(init=False)

    def __post_init__(self) -> None:
        """Determine if the metric has changed."""
        self.changed = self.before != self.after


@dataclass
class FileDiff:
    """Represents all metric diffs for a single file or function."""

    path: str
    metrics: list[MetricDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Determine if any metrics have changed."""
        return any(m.changed for m in self.metrics)


def _resolve_files_and_targets(
    config: WilyConfig,
    files: list[str],
) -> tuple[list[str], list[str]]:
    """
    Resolve target paths and expand directories to file paths.

    Returns:
        Tuple of (normalized file paths, absolute target paths for analysis)

    """
    # Resolve target paths when the cli has specified --path
    if config.path != DEFAULT_PATH:
        targets = [str(Path(config.path) / Path(file)) for file in files]
    else:
        targets = files

    # Expand directories to paths (normalize to Unix-style paths)
    normalized_files = [os.path.relpath(fn, config.path).replace("\\", "/") for fn in iter_filenames(targets)]
    logger.debug("Targeting - %s", normalized_files)

    return normalized_files, targets


def _resolve_metrics_and_operators(
    metrics: list[str] | None,
) -> tuple[list[Operator], list[tuple[str, Metric]]]:
    """
    Resolve which operators and metrics to use based on input.

    Returns:
        Tuple of (operators list, resolved metrics as (operator_name, Metric) tuples)

    """
    if metrics:
        operators = [resolve_operator(metric.split(".")[0]) for metric in metrics]
        resolved_metrics = [(metric.split(".")[0], resolve_metric(metric)) for metric in metrics]
    else:
        operators = list(ALL_OPERATORS.values())
        resolved_metrics = [(operator.name, metric) for operator, metric in ALL_METRICS if operator in operators]

    return operators, resolved_metrics


def _load_indexed_metrics(
    index: WilyIndex,
    files: list[str],
    revision: str | None,
) -> dict[str, dict[str, Any]]:
    """
    Load cached metrics from the index for the given files.

    Args:
        index: The WilyIndex to query
        files: List of file paths to load
        revision: Specific revision to load, or None for latest

    Returns:
        Dict mapping file path to dict of metric values

    """
    last_data: dict[str, dict[str, Any]] = defaultdict(dict)

    for file in files:
        path_rows = index[file]
        if not path_rows:
            continue

        if revision:
            data = next((row for row in path_rows if row.get("revision") == revision), None)
            if data is None:
                logger.error(f"Revision {revision} not found for {file}")
                raise SystemExit(1)
        else:
            data = path_rows[-1]

        # Copy all metric values (exclude metadata fields)
        for key, value in data.items():
            if key not in (
                "revision",
                "revision_date",
                "revision_author",
                "revision_message",
                "path",
                "path_type",
            ):
                last_data[file][key] = value

    return last_data


def _load_detailed_metrics(
    index: WilyIndex,
    current_data: dict[str, dict[str, Any]],
    files: list[str],
    revision: str | None,
) -> dict[str, dict[str, Any]]:
    """
    Load function/class level metrics from the index.

    Args:
        index: The WilyIndex to query
        current_data: Current analysis data containing detailed info
        files: List of file paths
        revision: Specific revision to load, or None for latest

    Returns:
        Dict mapping object paths (file:name) to dict of metric values

    """
    detailed_data: dict[str, dict[str, Any]] = defaultdict(dict)

    for file in files:
        file_data = current_data.get(file, {})
        detailed = file_data.get("detailed", {})

        for obj_name in detailed.keys():
            obj_path = f"{file}:{obj_name}"
            obj_rows = index[obj_path]

            if not obj_rows:
                continue

            if revision:
                obj_data = next((row for row in obj_rows if row.get("revision") == revision), None)
                if obj_data is None:
                    logger.error(f"Revision {revision} not found for {obj_path}")
                    raise SystemExit(1)
            else:
                obj_data = obj_rows[-1]

            for key, value in obj_data.items():
                if key not in (
                    "revision",
                    "revision_date",
                    "revision_author",
                    "revision_message",
                    "path",
                    "path_type",
                ):
                    detailed_data[obj_path][key] = value

    return detailed_data


def _get_current_metric_value(
    current_data: dict[str, dict[str, Any]],
    file_path: str,
    metric_name: str,
) -> Any:
    """
    Get metric value from current analysis data.

    Handles both file-level and function/class-level paths.
    """
    if ":" in file_path:
        # Function or class path like "src/foo.py:func_name"
        base_file, obj_name = file_path.rsplit(":", 1)
        file_data = current_data.get(base_file, {})
        detailed = file_data.get("detailed", {})
        obj_data = detailed.get(obj_name, {})
        return obj_data.get(metric_name)
    else:
        # File path
        file_data = current_data.get(file_path, {})
        return file_data.get(metric_name)


def _collect_detailed_paths(
    current_data: dict[str, dict[str, Any]],
    files: list[str],
    resolved_metrics: list[tuple[str, Metric]],
) -> set[str]:
    """
    Collect function/class paths from current analysis data.

    Only includes paths if the metrics include object-level operators.
    """
    extra_paths: set[str] = set()

    # Check if any operator has Object level (functions/classes)
    has_object_level = any(resolve_operator(operator).level == OperatorLevel.Object for operator, _ in resolved_metrics)

    if not has_object_level:
        return extra_paths

    for file in files:
        file_data = current_data.get(file, {})
        detailed = file_data.get("detailed", {})
        if detailed:
            for obj_name in detailed.keys():
                extra_paths.add(f"{file}:{obj_name}")

    return extra_paths


def _compute_file_diff(
    file_path: str,
    indexed_data: dict[str, dict[str, Any]],
    current_data: dict[str, dict[str, Any]],
    resolved_metrics: list[tuple[str, Metric]],
) -> FileDiff:
    """
    Compute metric diffs for a single file or function.

    Returns:
        FileDiff containing all metric comparisons

    """
    file_diff = FileDiff(path=file_path)

    for _, metric in resolved_metrics:
        # Get cached value
        before = indexed_data.get(file_path, {}).get(metric.name)

        # Get current value
        after = _get_current_metric_value(current_data, file_path, metric.name)

        file_diff.metrics.append(MetricDiff(name=metric.name, before=before, after=after, metric=metric))

    return file_diff


def _format_json_output(
    diffs: list[FileDiff],
    changes_only: bool,
) -> list[dict[str, Any]]:
    """
    Format diffs as JSON-serializable output.

    Args:
        diffs: List of FileDiff objects
        changes_only: If True, only include metrics that changed

    Returns:
        List of dicts ready for JSON serialization

    """
    results = []

    for file_diff in diffs:
        if changes_only and not file_diff.has_changes:
            continue

        file_entry: dict[str, Any] = {"file": file_diff.path, "metrics": {}}

        for metric_diff in file_diff.metrics:
            # Skip unchanged metrics if changes_only
            if changes_only and not metric_diff.changed:
                continue

            file_entry["metrics"][metric_diff.name] = {
                "before": metric_diff.before,
                "after": metric_diff.after,
            }

        # Only add if there are metrics to show
        if file_entry["metrics"]:
            results.append(file_entry)

    return results


def _format_table_cell(metric_diff: MetricDiff) -> str | Text:
    """Format a single metric diff as a table cell."""
    before = metric_diff.before
    after = metric_diff.after
    metric = metric_diff.metric

    # Handle missing values
    before_display = "-" if before is None else before
    after_display = "-" if after is None else after

    # Format numeric values with styling
    if metric.metric_type in (int, float) and before is not None and after is not None:
        cell = Text(f"{before_display:n} -> ")
        if before > after:
            cell.append(f"{after_display:n}", style=BAD_STYLES[metric.measure])
        elif before < after:
            cell.append(f"{after_display:n}", style=GOOD_STYLES[metric.measure])
        else:
            cell.append(f"{after_display:n}")
        return cell

    # Handle non-numeric or missing values
    if before_display == "-" and after_display == "-":
        return "-"
    return f"{before_display} -> {after_display}"


def _format_table_output(
    diffs: list[FileDiff],
    resolved_metrics: list[tuple[str, Metric]],
    changes_only: bool,
    wrap: bool,
    table_style: str,
) -> None:
    """
    Format and print diffs as a table.

    Args:
        diffs: List of FileDiff objects
        resolved_metrics: List of (operator_name, Metric) tuples for headers
        changes_only: If True, only include files with changes
        wrap: Whether to wrap table output
        table_style: Table box style

    """
    results = []

    for file_diff in diffs:
        if changes_only and not file_diff.has_changes:
            logger.debug("Skipping %s - no changes", file_diff.path)
            continue

        row = [file_diff.path]
        for metric_diff in file_diff.metrics:
            row.append(_format_table_cell(metric_diff))
        results.append(tuple(row))

    if results:
        headers = ("File", *(metric.description for _, metric in resolved_metrics))
        print_table(headers=headers, data=results, wrap=wrap, table_style=table_style)


def diff(
    config: WilyConfig,
    files: list[str],
    metrics: list[str] | None,
    changes_only: bool = True,
    detail: bool = True,
    revision: str | None = None,
    wrap: bool = False,
    table_style: str = DEFAULT_TABLE_STYLE,
    json: bool = False,
) -> None:
    """
    Show the differences in metrics for each of the files.

    :param config: The wily configuration
    :param files: The files to compare.
    :param metrics: The metrics to measure.
    :param changes_only: Only include changes files in output.
    :param detail: Show details (function-level)
    :param revision: Compare with specific revision (default: latest)
    :param wrap: Wrap output
    :param table_style: Table box style
    :param json: Output as JSON
    """
    config.targets = files
    archiver = config.archiver or DEFAULT_ARCHIVER

    # Resolve paths and expand directories
    files, targets = _resolve_files_and_targets(config, files)

    # Get path to parquet index
    parquet_path = get_default_metrics_path(config, archiver)
    if not Path(parquet_path).exists():
        logger.error("Wily cache not found. Run 'wily build' first.")
        sys.exit(1)

    # Determine which operators and metrics to use
    operators, resolved_metrics = _resolve_metrics_and_operators(metrics)
    operator_names = [op.name for op in operators]

    # Load indexed data and run current analysis
    with WilyIndex(parquet_path, operator_names) as index:
        # Load file-level metrics from index
        indexed_data = _load_indexed_metrics(index, files, revision)

        # Analyze current files
        current_data = index.analyze_files(targets, str(config.path), detail)

        # Load function/class metrics if detail mode
        if detail:
            detailed_indexed = _load_detailed_metrics(index, current_data, files, revision)
            indexed_data.update(detailed_indexed)

    # Add function/class paths to file list
    if detail:
        extra_paths = _collect_detailed_paths(current_data, files, resolved_metrics)
        files.extend(sorted(extra_paths))

    logger.debug(files)

    # Compute diffs for all files
    diffs = [_compute_file_diff(file, indexed_data, current_data, resolved_metrics) for file in files]

    # Output results
    if json:
        json_results = _format_json_output(diffs, changes_only)
        print(json_module.dumps(json_results, indent=2))
    else:
        _format_table_output(diffs, resolved_metrics, changes_only, wrap, table_style)
