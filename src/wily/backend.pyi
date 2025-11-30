from typing import Any

def harvest_maintainability_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest maintainability metrics from source files using Rust backend."""
    ...

def harvest_cyclomatic_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest cyclomatic complexity metrics from source files using Rust backend."""
    ...


def harvest_raw_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest raw metrics from source files using Rust backend."""
    ...
