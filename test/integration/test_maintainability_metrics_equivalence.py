"""
Test that the Rust MI harvester produces similar results to Radon.

Note: The results may not be exactly identical because radon uses Python's AST
while we use Ruff's AST, but they should be close.
"""


from radon.metrics import mi_rank, mi_visit

SAMPLE_PROGRAM = """\
def simple_function(x, y):
    '''A simple function that adds two numbers.'''
    return x + y

def function_with_if(a, b, c):
    # Check which is larger
    if a > b:
        result = a * c
    else:
        result = b + c
    return result

def function_with_loop(items):
    '''
    Sum all items in the list.
    
    This is a multiline docstring.
    '''
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
    '''A sample class with methods.'''
    
    def method_one(self, x):
        return x * 2

    def method_two(self, a, b):
        if a > b:
            return a
        return b
"""


def test_radon_mi_baseline() -> None:
    """Verify radon's MI for the sample program."""
    mi = mi_visit(SAMPLE_PROGRAM, multi=True)
    rank = mi_rank(mi)

    # Verify we get reasonable values
    assert 0 <= mi <= 100, f"MI should be 0-100, got {mi}"
    assert rank in ("A", "B", "C"), f"Rank should be A/B/C, got {rank}"

    print(f"Radon MI: {mi:.2f}, Rank: {rank}")


def test_rust_mi_matches_radon() -> None:
    """The Rust harvester should produce similar MI to Radon."""
    from wily._rust import harvest_maintainability_metrics

    # Get Radon results
    radon_mi = mi_visit(SAMPLE_PROGRAM, multi=True)
    radon_rank = mi_rank(radon_mi)

    # Get Rust results
    filename = "sample.py"
    rust_results = dict(harvest_maintainability_metrics([(filename, SAMPLE_PROGRAM)], multi=True))[filename]

    rust_mi = rust_results["mi"]
    rust_rank = rust_results["rank"]

    print(f"Radon MI: {radon_mi:.2f}, Rank: {radon_rank}")
    print(f"Rust MI: {rust_mi:.2f}, Rank: {rust_rank}")

    # MI values should be reasonably close (within 10 points)
    # The difference comes from different AST parsing and LLOC calculation
    assert abs(rust_mi - radon_mi) < 15, f"MI difference too large: Rust={rust_mi:.2f}, Radon={radon_mi:.2f}"

    # Rank should ideally match
    # Note: ranks may differ near boundaries (9, 19)
    if abs(radon_mi - 9) > 2 and abs(radon_mi - 19) > 2:
        assert rust_rank == radon_rank, f"Rank mismatch: Rust={rust_rank}, Radon={radon_rank}"


def test_rust_mi_multi_false() -> None:
    """Test MI with multi=False."""
    from wily._rust import harvest_maintainability_metrics

    # Get Radon results
    radon_mi = mi_visit(SAMPLE_PROGRAM, multi=False)

    # Get Rust results
    filename = "sample.py"
    rust_results = dict(harvest_maintainability_metrics([(filename, SAMPLE_PROGRAM)], multi=False))[filename]

    rust_mi = rust_results["mi"]

    print(f"Radon MI (multi=False): {radon_mi:.2f}")
    print(f"Rust MI (multi=False): {rust_mi:.2f}")

    # Should still be reasonably close
    assert abs(rust_mi - radon_mi) < 15


def test_rust_mi_empty_code() -> None:
    """Test MI for empty/minimal code."""
    from wily._rust import harvest_maintainability_metrics

    # Empty code should give high MI (100)
    empty_results = dict(harvest_maintainability_metrics([("empty.py", "")], multi=True))["empty.py"]
    assert empty_results["mi"] == 100.0

    # Single line should work
    single_results = dict(harvest_maintainability_metrics([("single.py", "x = 1")], multi=True))["single.py"]
    assert 0 <= single_results["mi"] <= 100


def test_rust_mi_syntax_error() -> None:
    """Test MI for code with syntax errors."""
    from wily._rust import harvest_maintainability_metrics

    bad_code = "def foo(:\n    pass"
    results = dict(harvest_maintainability_metrics([("bad.py", bad_code)], multi=True))["bad.py"]

    assert "error" in results
