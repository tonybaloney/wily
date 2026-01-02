from collections.abc import Collection
from types import TracebackType
from typing import Any

from wily.archivers import RevisionInfo


def iter_filenames(targets: list[str], include_ipynb: bool = False) -> list[str]:
    """Iterate over Python filenames in targets."""
    ...


def get_metrics_schema() -> list[tuple[str, str]]:
    """Get the parquet schema as a list of (name, type) tuples."""
    ...

class WilyIndex:
    """
    Python context manager for efficient multi-revision parquet writes.

    Usage:
        with WilyIndex(output_path, operators) as index:
            index.analyze_revision(paths, base_path, revision_key, ...)
            index.analyze_revision(paths, base_path, revision_key, ...)
        # File is written on exit

    Querying:
        with WilyIndex(output_path, operators) as index:
            # Get all rows for a specific path
            rows = index["src/foo.py"]

            # Iterate over all rows
            for row in index:
                print(row)

            # Get total row count
            count = len(index)
    """

    def __init__(self, output_path: str, operators: list[str]) -> None: ...

    def __enter__(self) -> WilyIndex: ...

    def __getitem__(self, path: str) -> list[dict[str, Any]]:
        """
        Get all rows matching the given path.

        Args:
            path: The file path to look up

        Returns:
            List of row dicts matching the path

        """
        ...

    def __iter__(self) -> WilyIndexIterator:
        """
        Iterate over all rows in the index.

        Returns:
            Iterator yielding row dicts

        """
        ...

    def __len__(self) -> int:
        """
        Get the total number of rows in the index.

        Returns:
            Total count of loaded + new rows

        """
        ...

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
        """
        Analyze a revision and accumulate results.

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

    def analyze_files(
        self,
        paths: list[str],
        base_path: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Analyze files and return metrics without storing to the index.

        This is useful for comparing uncommitted files against indexed values.

        Args:
            paths: List of absolute file paths to analyze
            base_path: Base path for computing relative paths

        Returns:
            Dict mapping relative paths to their metric dicts.
            Each metric dict contains:
            - path: relative path
            - path_type: "file"
            - Raw metrics: loc, sloc, lloc, comments, multi, blank, single_comments
            - Cyclomatic: complexity
            - Halstead: h1, h2, N1, N2, vocabulary, length, volume, difficulty, effort
            - Maintainability: mi, rank
            - detailed: dict of functions/classes with their metrics

        """
        ...


class RevisionIterator(Collection[RevisionInfo]):
    """Iterator over revisions in a Git repository."""

    def __iter__(self) -> RevisionIterator: ...
    def __next__(self) -> RevisionInfo: ...
    def __len__(self) -> int: ...


# Git functions
def get_revisions(path: str, max_revisions: int) -> RevisionIterator:
    """Get revisions from git repository."""
    ...

def checkout_revision(path: str, revision: str) -> None:
    """Checkout a specific revision."""
    ...

def checkout_branch(path: str, branch: str) -> None:
    """Checkout a branch."""
    ...

def find_revision(path: str, revision: str) -> RevisionInfo | None:
    """Find a revision by hash prefix."""
    ...


class WilyIndexIterator:
    """Iterator for WilyIndex rows."""

    def __iter__(self) -> WilyIndexIterator: ...
    def __next__(self) -> dict[str, Any]: ...

