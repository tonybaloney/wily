"""
Test that the Rust Halstead harvester produces identical results to Radon.

This test ensures backward compatibility - users migrating to the Rust backend
should see the same Halstead metrics as before.
"""

import ast
import math

from radon.metrics import halstead_visitor_report
from radon.visitors import HalsteadVisitor

from wily.backend import harvest_halstead_metrics

SAMPLE_PROGRAM = """\
def simple_function(x, y):
    return x + y

def function_with_if(a, b, c):
    if a > b:
        result = a * c
    else:
        result = b + c
    return result

def function_with_loop(items):
    total = 0
    for item in items:
        total += item
    return total

def function_with_multiple_ops(x, y, z):
    a = x + y
    b = y * z
    c = a - b
    return c / 2

class MyClass:
    def method_one(self, x):
        return x * 2

    def method_two(self, a, b):
        if a > b:
            return a
        return b
"""


def get_radon_results(source: str) -> dict:
    """Get Halstead metrics from radon."""
    visitor = HalsteadVisitor.from_ast(ast.parse(source))
    total_report = halstead_visitor_report(visitor)

    output = {
        "total": {
            "h1": total_report.h1,
            "h2": total_report.h2,
            "N1": total_report.N1,
            "N2": total_report.N2,
            "vocabulary": total_report.vocabulary,
            "length": total_report.length,
            "volume": total_report.volume,
            "difficulty": total_report.difficulty,
            "effort": total_report.effort,
        },
        "functions": {},
    }

    for v in visitor.function_visitors:
        report = halstead_visitor_report(v)
        output["functions"][v.context] = {
            "h1": report.h1,
            "h2": report.h2,
            "N1": report.N1,
            "N2": report.N2,
            "vocabulary": report.vocabulary,
            "length": report.length,
            "volume": report.volume,
            "difficulty": report.difficulty,
            "effort": report.effort,
        }

    return output


def test_radon_halstead_baseline() -> None:
    """Verify radon's Halstead metrics for the sample program.

    This test documents the expected values that the Rust implementation must match.
    """
    results = get_radon_results(SAMPLE_PROGRAM)

    # Verify we got results for all functions
    assert "simple_function" in results["functions"]
    assert "function_with_if" in results["functions"]
    assert "function_with_loop" in results["functions"]
    assert "function_with_multiple_ops" in results["functions"]
    assert "method_one" in results["functions"]
    assert "method_two" in results["functions"]

    # Verify basic metrics structure
    for name, func in results["functions"].items():
        assert func["h1"] >= 0  # unique operands
        assert func["h2"] >= 0  # unique operators
        assert func["N1"] >= 0  # total operands
        assert func["N2"] >= 0  # total operators
        assert func["vocabulary"] == func["h1"] + func["h2"]
        assert func["length"] == func["N1"] + func["N2"]

        # volume = length * log2(vocabulary)
        if func["vocabulary"] > 0:
            expected_volume = func["length"] * math.log2(func["vocabulary"])
            assert abs(func["volume"] - expected_volume) < 0.001, f"{name} volume mismatch"

        # effort = difficulty * volume
        expected_effort = func["difficulty"] * func["volume"]
        assert abs(func["effort"] - expected_effort) < 0.001, f"{name} effort mismatch"


def test_rust_halstead_matches_radon() -> None:
    """The Rust harvester should match Radon's Halstead metrics."""

    filename = "sample.py"
    rust_results = dict(harvest_halstead_metrics([(filename, SAMPLE_PROGRAM)]))[filename]
    radon_results = get_radon_results(SAMPLE_PROGRAM)

    # Compare total metrics
    for key in ["h1", "h2", "N1", "N2", "vocabulary", "length"]:
        assert rust_results["total"][key] == radon_results["total"][key], f"Total {key} mismatch: Rust={rust_results['total'][key]}, Radon={radon_results['total'][key]}"

    # Compare floating point metrics with tolerance
    for key in ["volume", "difficulty", "effort"]:
        rust_val = rust_results["total"][key]
        radon_val = radon_results["total"][key]
        assert abs(rust_val - radon_val) < 0.001, f"Total {key} mismatch: Rust={rust_val}, Radon={radon_val}"

    # Compare function metrics
    rust_funcs = rust_results["functions"]
    radon_funcs = radon_results["functions"]

    assert set(rust_funcs.keys()) == set(radon_funcs.keys()), f"Function names mismatch: Rust={set(rust_funcs.keys())}, Radon={set(radon_funcs.keys())}"

    for name in rust_funcs:
        for key in ["h1", "h2", "N1", "N2", "vocabulary", "length"]:
            assert rust_funcs[name][key] == radon_funcs[name][key], f"{name}.{key} mismatch: Rust={rust_funcs[name][key]}, Radon={radon_funcs[name][key]}"

        for key in ["volume", "difficulty", "effort"]:
            rust_val = rust_funcs[name][key]
            radon_val = radon_funcs[name][key]
            assert abs(rust_val - radon_val) < 0.001, f"{name}.{key} mismatch: Rust={rust_val}, Radon={radon_val}"
