from typing import Any
from types import TracebackType

def harvest_maintainability_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest maintainability metrics from source files using Rust backend."""
    ...

def harvest_cyclomatic_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest cyclomatic complexity metrics from source files using Rust backend."""
    ...


def harvest_raw_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest raw metrics from source files using Rust backend."""
    ...

def harvest_halstead_metrics(sources: list[tuple[str, str]]) -> list[tuple[str, dict[str, Any]]]:
    """Harvest halstead metrics from source files using Rust backend."""
    ...

def iter_filenames(targets: list[str], include_ipynb: bool = False) -> list[str]:
    """Iterate over Python filenames in targets."""
    ...

def analyze_files_parallel(
    paths: list[str],
    operators: list[str],
    multi: bool = False,
) -> dict[str, dict[str, Any]]:
    """Analyze files in parallel using Rust/rayon."""
    ...

def get_metrics_schema() -> list[tuple[str, str]]:
    """Get the parquet schema as a list of (name, type) tuples."""
    ...

class WilyIndex:
    """Python context manager for efficient multi-revision parquet writes.

    Usage:
        with WilyIndex(output_path, operators) as index:
            index.analyze_revision(paths, base_path, revision_key, ...)
            index.analyze_revision(paths, base_path, revision_key, ...)
        # File is written on exit
    """

    def __init__(self, output_path: str, operators: list[str]) -> None: ...

    def __enter__(self) -> "WilyIndex": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool: ...

    def analyze_revision(
        self,
        paths: list[str],
        base_path: str,
        revision_key: str,
        revision_date: int,
        revision_author: str | None,
        revision_message: str | None,
    ) -> int:
        """Analyze a revision and accumulate results.

        Args:
            paths: List of absolute file paths to analyze
            base_path: Base path for computing relative paths
            revision_key: Commit hash or revision identifier
            revision_date: Unix timestamp of the revision
            revision_author: Author name (optional)
            revision_message: Commit message (optional)

        Returns:
            Root LOC for this revision
        """
        ...

# Git functions
def get_revisions(path: str, max_revisions: int) -> list[dict[str, Any]]:
    """Get revisions from git repository."""
    ...

def checkout_revision(path: str, revision: str) -> None:
    """Checkout a specific revision."""
    ...

def checkout_branch(path: str, branch: str) -> None:
    """Checkout a branch."""
    ...

def find_revision(path: str, revision: str) -> dict[str, Any] | None:
    """Find a revision by hash prefix."""
    ...
