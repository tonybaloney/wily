import json
import pathlib
from textwrap import dedent

from click.testing import CliRunner

import wily.__main__ as main

_path = "src/test.py"


def test_diff_no_cache(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "diff", _path], catch_exceptions=False)
    assert result.exit_code == 1, result.stdout


def test_diff_no_path(tmpdir):
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "diff"], catch_exceptions=False)
    assert result.exit_code == 2, result.stdout


def test_diff_output(builddir):
    """Test the diff feature with no changes"""
    runner = CliRunner()
    # Don't use --debug since debug logs now contain the filename
    result = runner.invoke(main.cli, ["--path", builddir, "diff", _path], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_all(builddir):
    """Test the diff feature with no changes and the --all flag"""
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout


def test_diff_output_all_wrapped(builddir):
    """Test the diff feature with wrapping"""
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all", "--wrap"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout


def test_diff_output_bad_path(builddir):
    """Test the diff feature with no changes"""
    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", "src/baz.py"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" not in result.stdout


def test_diff_output_remove_all(builddir):
    """Test the diff feature by removing all functions and classes"""

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write("print(1)")

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--debug", "--path", builddir, "diff", _path, "--all"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout


def test_diff_output_more_complex(builddir):
    """Test the diff feature by making the test file more complicated"""

    complex_test = """
            import abc
            foo = 1
            def function1():
                a = 1 + 1
                if a == 2:
                    print(1)
            class Class1(object):
                def method(self):
                    b = 1 + 5
                    if b == 6:
                        if 1==2:
                           if 2==3:
                              print(1)
            """

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(complex_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "diff", _path, "--all", "--json"],
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)  # Verify valid JSON output
    assert len(data) > 0
    assert data[0]['file'] == "src/test.py"
    assert data[0]['complexity'] == "6 -> 11"


def test_diff_output_less_complex(builddir):
    """Test the diff feature by making the test file less complicated"""

    simple_test = """
            import abc
            foo = 1
            def function1():
                pass
            class Class1(object):
                def method(self):
                    pass
            """

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "diff", _path, "--all", "--json"],
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)  # Verify valid JSON output
    assert len(data) > 0
    assert data[0]['file'] == "src/test.py"
    assert data[0]['complexity'] == "6 -> 4"


def test_diff_output_loc(builddir):
    """Test the diff feature by making the test file more complicated"""

    simple_test = """print("test")"""

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        ["--path", builddir, "diff", _path, "--metrics", "raw.loc", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    data = json.loads(result.stdout)  # Verify valid JSON output
    assert len(data) > 0
    assert "test.py" in result.stdout
    assert "11 -> 1" in result.stdout


def test_diff_output_rank(builddir):
    """Test the diff feature by making the test file more complicated"""

    simple_test = """print("test")"""

    with open(pathlib.Path(builddir) / "src" / "test.py", "w") as test_py:
        test_py.write(dedent(simple_test))

    runner = CliRunner()
    result = runner.invoke(
        main.cli,
        [
            "--debug",
            "--path",
            builddir,
            "diff",
            _path,
            "--all",
            "--metrics",
            "maintainability.rank",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    assert "test.py" in result.stdout
    assert "A -> A" in result.stdout


# TODO: Test diff with details
# TODO: Test diff with multiple files


def test_diff_only_shows_changed_functions(tmpdir):
    """
    Test that diff only shows functions/classes that have actually changed.
    
    This is a regression test for a bug where all functions/classes were shown
    as having changed even when only one was modified.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    # Initial code with two distinct functions
    initial_code = dedent("""
        def unchanged_function():
            '''This function will not be modified'''
            x = 1
            return x

        def changed_function():
            '''This function will be modified'''
            y = 2
            return y
        
        class UnchangedClass:
            def method(self):
                return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    # Initialize git repo
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    # Build wily index
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Modify ONLY changed_function - add complexity
    modified_code = dedent("""
        def unchanged_function():
            '''This function will not be modified'''
            x = 1
            return x

        def changed_function():
            '''This function will be modified'''
            y = 2
            if y > 1:
                y = y + 1
            return y
        
        class UnchangedClass:
            def method(self):
                return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    # Run diff with JSON output
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    # Collect which entries show changes
    changed_entries = [entry["file"] for entry in data]
    
    # The file itself should show changes (file-level metrics changed)
    assert "src/test.py" in changed_entries
    
    # changed_function should show in diff (complexity increased)
    assert "src/test.py:changed_function" in changed_entries
    
    # unchanged_function should NOT show in diff - it wasn't modified!
    assert "src/test.py:unchanged_function" not in changed_entries, \
        f"unchanged_function should not appear in diff, but found entries: {changed_entries}"
    
    # UnchangedClass and its method should NOT show in diff
    assert "src/test.py:UnchangedClass" not in changed_entries, \
        f"UnchangedClass should not appear in diff, but found entries: {changed_entries}"
    assert "src/test.py:UnchangedClass.method" not in changed_entries, \
        f"UnchangedClass.method should not appear in diff, but found entries: {changed_entries}"
    
    repo.close()


def test_diff_no_duplicate_entries(tmpdir):
    """
    Test that diff doesn't show duplicate entries for functions/classes.
    
    This is a regression test for a bug where each function/class appeared
    multiple times in the output (once per operator).
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    # Initial code
    initial_code = dedent("""
        def my_function():
            x = 1
            return x
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    # Initialize git repo
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    # Build wily index
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Modify the function - add complexity
    modified_code = dedent("""
        def my_function():
            x = 1
            if x > 0:
                x = x + 1
            return x
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    # Run diff with JSON output
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    # Count occurrences of each file entry
    file_counts = {}
    for entry in data:
        file_path = entry["file"]
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    # Each file/function/class should appear at most once
    for file_path, count in file_counts.items():
        assert count == 1, \
            f"{file_path} appears {count} times in diff output, expected 1. Full output: {data}"
    
    repo.close()


def test_diff_with_multiple_functions_only_changed_shown(tmpdir):
    """
    Test that when multiple functions exist but only some change,
    only the changed ones appear in the diff output (without --all flag).
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    # Initial code with multiple functions
    initial_code = dedent("""
        def func_a():
            return 1
        
        def func_b():
            return 2
        
        def func_c():
            return 3
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Modify ONLY func_b - add complexity
    modified_code = dedent("""
        def func_a():
            return 1
        
        def func_b():
            x = 2
            if x > 1:
                return x + 1
            return 2
        
        def func_c():
            return 3
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    # Run diff (changes_only=True by default)
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    changed_files = [entry["file"] for entry in data]
    
    # File-level should show (total metrics changed)
    assert "src/test.py" in changed_files
    
    # Only func_b should show as changed
    assert "src/test.py:func_b" in changed_files
    
    # func_a and func_c should NOT appear (no changes)
    assert "src/test.py:func_a" not in changed_files, \
        f"func_a should not appear, got: {changed_files}"
    assert "src/test.py:func_c" not in changed_files, \
        f"func_c should not appear, got: {changed_files}"
    
    repo.close()


def test_diff_with_classes_and_methods(tmpdir):
    """
    Test diff output with classes and methods - no duplicates, only changed items.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    # Initial code with class
    initial_code = dedent("""
        class MyClass:
            def method_a(self):
                return 1
            
            def method_b(self):
                return 2
        
        def standalone_func():
            return 3
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Modify only method_b
    modified_code = dedent("""
        class MyClass:
            def method_a(self):
                return 1
            
            def method_b(self):
                x = 2
                if x > 1:
                    return x * 2
                return 2
        
        def standalone_func():
            return 3
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    # Check for no duplicates
    file_counts = {}
    for entry in data:
        file_path = entry["file"]
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    for file_path, count in file_counts.items():
        assert count == 1, f"{file_path} appears {count} times"
    
    changed_files = list(file_counts.keys())
    
    # method_b changed, so MyClass total complexity changed
    assert "src/test.py:MyClass.method_b" in changed_files
    assert "src/test.py:MyClass" in changed_files  # Class aggregate changed
    
    # These should NOT appear (unchanged)
    assert "src/test.py:MyClass.method_a" not in changed_files
    assert "src/test.py:standalone_func" not in changed_files
    
    repo.close()


def test_diff_all_flag_shows_unchanged_items(tmpdir):
    """
    Test that --all flag shows items even when they haven't changed.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    initial_code = dedent("""
        def func_a():
            return 1
        
        def func_b():
            return 2
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Modify only func_b
    modified_code = dedent("""
        def func_a():
            return 1
        
        def func_b():
            x = 2
            if x > 1:
                return x + 1
            return 2
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    # Run diff with --all flag
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--all", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    # No duplicates even with --all
    file_counts = {}
    for entry in data:
        file_path = entry["file"]
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    for file_path, count in file_counts.items():
        assert count == 1, f"{file_path} appears {count} times with --all flag"
    
    changed_files = list(file_counts.keys())
    
    # With --all, both functions should appear
    assert "src/test.py" in changed_files
    assert "src/test.py:func_a" in changed_files  # Shown because of --all
    assert "src/test.py:func_b" in changed_files  # Shown because it changed
    
    repo.close()


def test_diff_specific_metric_filters_output(tmpdir):
    """
    Test that specifying a metric filters the output appropriately.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    initial_code = dedent("""
        def my_func():
            return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    modified_code = dedent("""
        def my_func():
            x = 1
            if x > 0:
                return x + 1
            return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    # Run diff with only cyclomatic.complexity metric
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--metrics", "cyclomatic.complexity", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    # Should have entries
    assert len(data) > 0
    
    # Each entry should only have 'file' and 'complexity' keys
    for entry in data:
        assert "file" in entry
        assert "complexity" in entry
        # Should not have other metrics
        assert "mi" not in entry
        assert "loc" not in entry
    
    # No duplicates
    file_counts = {}
    for entry in data:
        file_path = entry["file"]
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    for file_path, count in file_counts.items():
        assert count == 1, f"{file_path} appears {count} times"
    
    repo.close()


def test_diff_new_function_added(tmpdir):
    """
    Test diff when a new function is added to an existing file.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    initial_code = dedent("""
        def existing_func():
            return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Add a new function
    modified_code = dedent("""
        def existing_func():
            return 1
        
        def new_func():
            x = 1
            if x > 0:
                return x + 1
            return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    changed_files = [entry["file"] for entry in data]
    
    # File-level should change (new function adds to totals)
    assert "src/test.py" in changed_files
    
    # New function should appear (it's new, so metrics go from None/- to values)
    assert "src/test.py:new_func" in changed_files
    
    # existing_func should NOT appear (unchanged)
    assert "src/test.py:existing_func" not in changed_files
    
    # No duplicates
    file_counts = {}
    for entry in data:
        file_path = entry["file"]
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    for file_path, count in file_counts.items():
        assert count == 1, f"{file_path} appears {count} times"
    
    repo.close()


def test_diff_function_removed(tmpdir):
    """
    Test diff when a function is removed from an existing file.
    """
    from git.repo.base import Repo
    from git.util import Actor
    
    tmppath = pathlib.Path(tmpdir)
    srcpath = tmppath / "src"
    srcpath.mkdir()
    testpath = srcpath / "test.py"
    
    initial_code = dedent("""
        def func_to_keep():
            return 1
        
        def func_to_remove():
            return 2
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(initial_code)
    
    repo = Repo.init(path=tmpdir)
    author = Actor("Test", "test@example.com")
    repo.index.add([str(testpath)])
    repo.index.commit("initial", author=author, committer=author)
    
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--path", tmpdir, "build", str(srcpath)])
    assert result.exit_code == 0, result.stdout
    
    # Remove func_to_remove
    modified_code = dedent("""
        def func_to_keep():
            return 1
    """).strip()
    
    with open(testpath, "w") as f:
        f.write(modified_code)
    
    result = runner.invoke(
        main.cli,
        ["--path", tmpdir, "diff", "src/test.py", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    
    changed_files = [entry["file"] for entry in data]
    
    # File-level should change
    assert "src/test.py" in changed_files
    
    # func_to_keep should NOT appear (unchanged)
    assert "src/test.py:func_to_keep" not in changed_files
    
    # Note: func_to_remove won't appear because it's not in current_data
    # (it no longer exists in the file)
    
    repo.close()


