import statistics
import sys

import pytest

from wily.archivers import Archiver, BaseArchiver, Revision
from wily.config import DEFAULT_CONFIG
from wily.operators import BaseOperator, Metric, MetricType, Operator, OperatorLevel


class MockArchiverCls(BaseArchiver):
    name = "test"

    def __init__(self, *args, **kwargs):
        pass

    def revisions(self, path, max_revisions):
        return [
            Revision(
                key="12345",
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=12_345_679,
                message="None",
                tracked_files=["a", "b", "c"],
                tracked_dirs=["d"],
                added_files=[],
                modified_files=[],
                deleted_files=[],
            ),
            Revision(
                key="67890",
                author_name="Local User",  # Don't want to leak local data
                author_email="-",  # as above
                date=12_345_679,
                message="None again",
                tracked_files=["a", "b", "c", "d"],
                tracked_dirs=["d"],
                added_files=["e"],
                modified_files=["f"],
                deleted_files=["a"],
            ),
        ]

    def checkout(self, revision, options):
        pass  # noop


class MockOperatorCls(BaseOperator):
    name = "test"
    data = {"C:\\home\\test1.py" if sys.platform == "win32" else "/home/test1.py": None}

    def __init__(self, *args, **kwargs):
        pass

    def run(self, module, options):
        return self.data


MockOperator = Operator("mock", MockOperatorCls, "for testing", OperatorLevel.File)

MockArchiver = Archiver("mock", MockArchiverCls, "for testing")


@pytest.fixture
def config():
    cfg = DEFAULT_CONFIG
    return cfg


class TestSeedCopyLogic:
    """Tests for the logic that copies data from unchanged files between revisions."""

    def test_seed_copy_includes_unchanged_files(self):
        """When processing a non-seed revision, unchanged files should be copied from prev_stats."""
        # Simulate previous revision data
        prev_stats = {
            "operator_data": {
                "raw": {
                    "file1.py": {"total": {"loc": 100}},
                    "file2.py": {"total": {"loc": 200}},
                    "file3.py": {"total": {"loc": 300}},
                }
            }
        }

        # Current revision only analyzed file1.py (modified)
        result = {
            "file1.py": {"total": {"loc": 150}},  # Modified file, new data
        }

        # Simulate the seed copy logic from build.py lines 150-162
        seed = False
        operator_name = "raw"
        tracked_files = ["file1.py", "file2.py", "file3.py"]
        tracked_dirs = []
        deleted_files = []

        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        assert "file1.py" in result
        assert "file2.py" in result
        assert "file3.py" in result
        assert result["file1.py"]["total"]["loc"] == 150
        assert result["file2.py"]["total"]["loc"] == 200
        assert result["file3.py"]["total"]["loc"] == 300

    def test_seed_copy_excludes_deleted_files(self):
        """Deleted files should be removed from results."""
        prev_stats = {
            "operator_data": {
                "raw": {
                    "file1.py": {"total": {"loc": 100}},
                    "file2.py": {"total": {"loc": 200}},
                }
            }
        }

        result = {}

        seed = False
        operator_name = "raw"
        tracked_files = ["file1.py"]
        tracked_dirs = []
        deleted_files = ["file2.py"]

        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        assert "file1.py" in result
        assert "file2.py" not in result

    def test_seed_copy_skips_directories(self):
        """Directories should not be copied as file results."""
        prev_stats = {
            "operator_data": {
                "raw": {
                    "src": {"total": {"loc": 500}},
                    "src/file1.py": {"total": {"loc": 100}},
                }
            }
        }

        result = {}

        seed = False
        operator_name = "raw"
        tracked_files = ["src", "src/file1.py"]
        tracked_dirs = ["src"]
        deleted_files = []

        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        assert "src/file1.py" in result
        assert "src" not in result

    def test_seed_revision_does_not_copy(self):
        """On seed revision, no copying should occur."""
        prev_stats = {
            "operator_data": {
                "raw": {
                    "file1.py": {"total": {"loc": 100}},
                }
            }
        }

        result = {
            "file2.py": {"total": {"loc": 200}},
        }

        seed = True
        operator_name = "raw"
        tracked_files = ["file1.py", "file2.py"]
        tracked_dirs = []
        deleted_files = []

        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        assert "file1.py" not in result
        assert "file2.py" in result


class TestAggregateMetricsLogic:
    """Tests for the logic that aggregates metrics across directories."""

    def test_aggregate_with_sum(self):
        """Test aggregation using sum (used by raw metrics like loc)."""
        result = {
            "src/file1.py": {"total": {"loc": 100, "sloc": 80}},
            "src/file2.py": {"total": {"loc": 200, "sloc": 150}},
            "src/sub/file3.py": {"total": {"loc": 50, "sloc": 40}},
        }

        # Define metrics with sum aggregation
        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
            Metric("sloc", "Source Lines of Code", int, MetricType.AimLow, sum),
        ]

        tracked_dirs = ["src", "src/sub"]
        dirs = [""] + [str(d) for d in tracked_dirs if d]

        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # Root aggregate should sum all files
        assert result[""]["total"]["loc"] == 350  # 100 + 200 + 50
        assert result[""]["total"]["sloc"] == 270  # 80 + 150 + 40

        # src directory should include all src/* files
        assert result["src"]["total"]["loc"] == 350
        assert result["src"]["total"]["sloc"] == 270

        # src/sub should only include src/sub/* files
        assert result["src/sub"]["total"]["loc"] == 50
        assert result["src/sub"]["total"]["sloc"] == 40

    def test_aggregate_with_mean(self):
        """Test aggregation using mean (used by cyclomatic complexity, MI)."""
        result = {
            "src/file1.py": {"total": {"complexity": 5.0}},
            "src/file2.py": {"total": {"complexity": 10.0}},
            "src/file3.py": {"total": {"complexity": 15.0}},
        }

        metrics = [
            Metric("complexity", "Cyclomatic Complexity", float, MetricType.AimLow, statistics.mean),
        ]

        tracked_dirs = ["src"]
        dirs = [""] + [str(d) for d in tracked_dirs if d]

        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # Mean of 5, 10, 15 = 10
        assert result[""]["total"]["complexity"] == 10.0
        assert result["src"]["total"]["complexity"] == 10.0

    def test_aggregate_nested_directories(self):
        """Test that nested directories aggregate correctly."""
        result = {
            "a/b/c/file1.py": {"total": {"loc": 100}},
            "a/b/file2.py": {"total": {"loc": 200}},
            "a/file3.py": {"total": {"loc": 300}},
            "other/file4.py": {"total": {"loc": 400}},
        }

        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
        ]

        tracked_dirs = ["a", "a/b", "a/b/c", "other"]
        dirs = [""] + [str(d) for d in tracked_dirs if d]

        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # Root includes all
        assert result[""]["total"]["loc"] == 1000

        # a/ includes a/*, a/b/*, a/b/c/*
        assert result["a"]["total"]["loc"] == 600  # 100 + 200 + 300

        # a/b includes a/b/*, a/b/c/*
        assert result["a/b"]["total"]["loc"] == 300  # 100 + 200

        # a/b/c includes only a/b/c/*
        assert result["a/b/c"]["total"]["loc"] == 100

        # other includes only other/*
        assert result["other"]["total"]["loc"] == 400

    def test_aggregate_skips_missing_metrics(self):
        """Files missing a metric should not cause errors."""
        result = {
            "file1.py": {"total": {"loc": 100, "complexity": 5}},
            "file2.py": {"total": {"loc": 200}},  # No complexity metric
        }

        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
            Metric("complexity", "Cyclomatic Complexity", float, MetricType.AimLow, statistics.mean),
        ]

        tracked_dirs = []
        dirs = [""] + [str(d) for d in tracked_dirs if d]

        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # loc should sum both files
        assert result[""]["total"]["loc"] == 300

        # complexity should only include file1.py
        assert result[""]["total"]["complexity"] == 5

    def test_aggregate_empty_directory(self):
        """Empty directories should have empty totals."""
        result = {
            "src/file1.py": {"total": {"loc": 100}},
        }

        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
        ]

        tracked_dirs = ["src", "empty"]  # empty has no files
        dirs = [""] + [str(d) for d in tracked_dirs if d]

        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        assert result["src"]["total"]["loc"] == 100
        assert "loc" not in result["empty"]["total"]  # No files, no aggregate


# ============================================================================
# Tests for combined seed copy + aggregation
# ============================================================================


class TestCombinedSeedAndAggregate:
    """Tests that verify the complete flow of seed copy followed by aggregation."""

    def test_full_flow_second_revision(self):
        """Test complete flow: copy unchanged files, then aggregate."""
        # Previous revision had 3 files
        prev_stats = {
            "operator_data": {
                "raw": {
                    "src/file1.py": {"total": {"loc": 100}},
                    "src/file2.py": {"total": {"loc": 200}},
                    "src/file3.py": {"total": {"loc": 300}},
                    "src": {"total": {"loc": 600}},  # Previous aggregate
                    "": {"total": {"loc": 600}},
                }
            }
        }

        # Current revision only modified file1.py
        result = {
            "src/file1.py": {"total": {"loc": 150}},  # Changed from 100 to 150
        }

        # Step 1: Seed copy
        seed = False
        operator_name = "raw"
        tracked_files = ["src/file1.py", "src/file2.py", "src/file3.py"]
        tracked_dirs = ["src"]
        deleted_files = []

        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        # Verify seed copy worked
        assert result["src/file1.py"]["total"]["loc"] == 150  # New value
        assert result["src/file2.py"]["total"]["loc"] == 200  # Copied
        assert result["src/file3.py"]["total"]["loc"] == 300  # Copied

        # Step 2: Aggregation
        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
        ]

        dirs = [""] + [str(d) for d in tracked_dirs if d]
        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # New aggregate should reflect the change: 150 + 200 + 300 = 650
        assert result["src"]["total"]["loc"] == 650
        assert result[""]["total"]["loc"] == 650

    def test_full_flow_with_deletion(self):
        """Test flow when a file is deleted between revisions."""
        prev_stats = {
            "operator_data": {
                "raw": {
                    "src/file1.py": {"total": {"loc": 100}},
                    "src/file2.py": {"total": {"loc": 200}},
                    "src/deleted.py": {"total": {"loc": 500}},
                }
            }
        }

        result = {}  # No new files analyzed

        seed = False
        operator_name = "raw"
        tracked_files = ["src/file1.py", "src/file2.py"]  # deleted.py removed
        tracked_dirs = ["src"]
        deleted_files = ["src/deleted.py"]

        # Seed copy
        indices = set(result.keys())
        if not seed:
            files = {str(f) for f in tracked_files}
            missing_indices = files - indices
            for missing in missing_indices:
                if missing in tracked_dirs:
                    continue
                if operator_name not in prev_stats["operator_data"]:
                    continue
                if missing not in prev_stats["operator_data"][operator_name]:
                    continue
                result[missing] = prev_stats["operator_data"][operator_name][missing]
            for deleted in deleted_files:
                result.pop(deleted, None)

        # Aggregation
        metrics = [
            Metric("loc", "Lines of Code", int, MetricType.Informational, sum),
        ]

        dirs = [""] + [str(d) for d in tracked_dirs if d]
        for root in sorted(dirs):
            aggregates = [p for p in result.keys() if p.startswith(root)]
            result[str(root)] = {"total": {}}
            for metric in metrics:
                values = [
                    result[agg]["total"][metric.name]
                    for agg in aggregates
                    if agg in result and metric.name in result[agg].get("total", {})
                ]
                if values:
                    result[str(root)]["total"][metric.name] = metric.aggregate(values)

        # deleted.py should not be included
        assert "src/deleted.py" not in result
        assert result["src"]["total"]["loc"] == 300  # 100 + 200, not 800
