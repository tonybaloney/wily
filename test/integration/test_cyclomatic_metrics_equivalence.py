"""
Test that the Rust cyclomatic complexity harvester produces identical results to Radon.

This test ensures backward compatibility - users migrating to the Rust backend
should see the same cyclomatic complexity metrics as before.
"""

from radon.complexity import cc_visit
from radon.visitors import Class, Function

# We'll import from Rust once implemented
# from wily._rust import harvest_cyclomatic_metrics

SAMPLE_PROGRAM = """\
def simple_function():
    return 42

def function_with_if(x):
    if x > 0:
        return "positive"
    return "non-positive"

def function_with_if_else(x):
    if x > 0:
        return "positive"
    else:
        return "non-positive"

def function_with_elif(x):
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"

def function_with_for(items):
    total = 0
    for item in items:
        total += item
    return total

def function_with_for_else(items):
    for item in items:
        if item < 0:
            return "found negative"
    else:
        return "all positive"

def function_with_while(x):
    while x > 0:
        x -= 1
    return x

def function_with_try(x):
    try:
        return int(x)
    except ValueError:
        return 0
    except TypeError:
        return -1

def function_with_and_or(a, b, c):
    if a and b or c:
        return True
    return False

def function_with_comprehension(items):
    return [x for x in items if x > 0]

def function_with_ternary(x):
    return "positive" if x > 0 else "non-positive"

class SimpleClass:
    def method_one(self):
        return 1

    def method_two(self, x):
        if x:
            return x
        return 0

class ComplexClass:
    def __init__(self, value):
        self.value = value

    def process(self, x):
        if x > 0:
            for i in range(x):
                if i % 2 == 0:
                    self.value += i
        return self.value

def nested_function():
    def inner():
        return 1
    return inner()
"""


def get_radon_results(source: str) -> dict:
    """Get cyclomatic complexity results from radon."""
    results = cc_visit(source)
    output = {"functions": [], "classes": []}

    for item in results:
        if isinstance(item, Function):
            output["functions"].append(
                {
                    "name": item.name,
                    "lineno": item.lineno,
                    "endline": item.endline,
                    "complexity": item.complexity,
                    "is_method": item.is_method,
                    "classname": item.classname,
                    "fullname": item.fullname,
                }
            )
        elif isinstance(item, Class):
            output["classes"].append(
                {
                    "name": item.name,
                    "lineno": item.lineno,
                    "endline": item.endline,
                    "complexity": item.complexity,
                    "real_complexity": item.real_complexity,
                    "methods": [
                        {
                            "name": m.name,
                            "lineno": m.lineno,
                            "endline": m.endline,
                            "complexity": m.complexity,
                            "is_method": m.is_method,
                            "classname": m.classname,
                            "fullname": m.fullname,
                        }
                        for m in item.methods
                    ],
                }
            )

    return output


def test_radon_cyclomatic_baseline() -> None:
    """Verify radon's cyclomatic complexity results for the sample program.

    This test documents the expected values that the Rust implementation must match.
    """
    results = get_radon_results(SAMPLE_PROGRAM)

    # Extract function complexities by name for easy lookup
    func_complexity = {f["fullname"]: f["complexity"] for f in results["functions"]}

    # Document expected complexities based on radon's calculation:
    # simple_function: 1 (no branches)
    assert func_complexity["simple_function"] == 1

    # function_with_if: 2 (1 + 1 if)
    assert func_complexity["function_with_if"] == 2

    # function_with_if_else: 2 (1 + 1 if, else doesn't add)
    assert func_complexity["function_with_if_else"] == 2

    # function_with_elif: 3 (1 + 1 if + 1 elif)
    assert func_complexity["function_with_elif"] == 3

    # function_with_for: 2 (1 + 1 for)
    assert func_complexity["function_with_for"] == 2

    # function_with_for_else: 4 (1 + 1 for + 1 for-else + 1 if)
    assert func_complexity["function_with_for_else"] == 4

    # function_with_while: 2 (1 + 1 while)
    assert func_complexity["function_with_while"] == 2

    # function_with_try: 3 (1 + 2 except handlers)
    assert func_complexity["function_with_try"] == 3

    # function_with_and_or: 4 (1 + 1 if + 1 and + 1 or)
    assert func_complexity["function_with_and_or"] == 4

    # function_with_comprehension: 3 (1 + 1 comprehension + 1 if in comprehension)
    assert func_complexity["function_with_comprehension"] == 3

    # function_with_ternary: 2 (1 + 1 ternary/IfExp)
    assert func_complexity["function_with_ternary"] == 2

    # Class methods
    class_results = {c["name"]: c for c in results["classes"]}

    # SimpleClass: methods have complexity 1 and 2
    simple_class = class_results["SimpleClass"]
    method_complexity = {m["name"]: m["complexity"] for m in simple_class["methods"]}
    assert method_complexity["method_one"] == 1
    assert method_complexity["method_two"] == 2

    # ComplexClass: __init__ is 1, process has nested loops/ifs
    complex_class = class_results["ComplexClass"]
    method_complexity = {m["name"]: m["complexity"] for m in complex_class["methods"]}
    assert method_complexity["__init__"] == 1
    assert method_complexity["process"] == 4  # 1 + 1 if + 1 for + 1 if


def test_rust_cyclomatic_matches_radon() -> None:
    """The Rust harvester should match Radon's cyclomatic complexity metrics."""
    from wily.backend import harvest_cyclomatic_metrics

    filename = "sample.py"
    rust_results = dict(harvest_cyclomatic_metrics([(filename, SAMPLE_PROGRAM)]))[filename]
    radon_results = get_radon_results(SAMPLE_PROGRAM)

    # Compare function complexities
    rust_funcs = {f["fullname"]: f for f in rust_results["functions"]}
    radon_funcs = {f["fullname"]: f for f in radon_results["functions"]}

    assert set(rust_funcs.keys()) == set(radon_funcs.keys()), "Function names should match"

    for name in rust_funcs:
        assert rust_funcs[name]["complexity"] == radon_funcs[name]["complexity"], f"Complexity mismatch for {name}: Rust={rust_funcs[name]['complexity']}, Radon={radon_funcs[name]['complexity']}"
        assert rust_funcs[name]["lineno"] == radon_funcs[name]["lineno"], f"Line number mismatch for {name}"

    # Compare class complexities
    rust_classes = {c["name"]: c for c in rust_results["classes"]}
    radon_classes = {c["name"]: c for c in radon_results["classes"]}

    assert set(rust_classes.keys()) == set(radon_classes.keys()), "Class names should match"

    for name in rust_classes:
        assert rust_classes[name]["complexity"] == radon_classes[name]["complexity"], f"Class complexity mismatch for {name}"
        assert rust_classes[name]["real_complexity"] == radon_classes[name]["real_complexity"], f"Class real_complexity mismatch for {name}"
