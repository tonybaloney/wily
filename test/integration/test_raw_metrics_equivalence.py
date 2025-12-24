"""Integration tests for comparing Rust and legacy raw metrics implementations."""

from __future__ import annotations

import textwrap

from radon.raw import analyze

from wily.backend import harvest_raw_metrics

SAMPLE_PROGRAM = textwrap.dedent(
    '''
    class Sample:
        def foo(self):
            """Docstring that should count toward logical metrics."""
            value = 41
            value += 1  # inline comment
            return value

        def bar(self):
            # A standalone comment line
            return "bar"


    def top_level():
        # One more comment to round things out
        return Sample()
    '''
).strip()

EXPECTED_KEYS = ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments")


def test_rust_raw_metrics_matches_radon_defaults() -> None:
    """The Rust harvester should match Radon's raw metrics for a simple module."""
    filename = "sample.py"
    rust_results = dict(harvest_raw_metrics([(filename, SAMPLE_PROGRAM)]))[filename]

    analysis = analyze(SAMPLE_PROGRAM)
    legacy_results = {key: getattr(analysis, key) for key in EXPECTED_KEYS}

    assert rust_results == legacy_results
