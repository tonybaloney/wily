# AGENTS.md

## Project Overview

**Wily** is a Python CLI tool for tracking, reporting on, and graphing code complexity metrics across git history. It analyzes Python source code using operators (cyclomatic complexity, Halstead metrics, maintainability index, raw line counts) and stores results in a Parquet-based cache.

**Architecture**: Hybrid Python + Rust (PyO3/maturin). The performance-critical backend (parsing, metric computation, Parquet storage, git operations) is written in Rust and exposed to Python as a native extension module (`wily.backend`). The CLI, configuration, command orchestration, and output formatting are in Python.

**Current branch**: `v2` (major rewrite from v1 — uses Rust backend + Parquet storage instead of pure Python + JSON).

## Commands

### Setup & Build

```bash
# Install for development (compiles Rust backend + installs Python package)
uv sync --all-groups
maturin develop

# Build release wheel
maturin build --release
```

### Testing

```bash
# Run all tests (unit + integration) with coverage
uv run pytest

# Run a specific test file
uv run pytest test/unit/test_operators.py

# Run a specific test
uv run pytest test/integration/test_build.py::test_build -v
```

- Test framework: **pytest ~7.2** with `pytest-cov`
- Test directory: `test/` (configured in `pyproject.toml` under `[tool.pytest.ini_options]`)
- Tests use `click.testing.CliRunner` for CLI integration tests
- Fixtures in `test/conftest.py` provide `gitdir` (git repo with 3 commits), `builddir` (gitdir + wily cache), and ipynb variants
- The `cache_path` fixture (autouse) creates a temp HOME to isolate wily cache per test
- Coverage config in `setup.cfg` under `[coverage:run]`

### Linting

```bash
# Python linting
uv tool run ruff check .

# Rust linting
cargo clippy --manifest-path backend/Cargo.toml -- -D warnings

# Rust formatting check
cargo fmt --manifest-path backend/Cargo.toml --check
```

- Python linter: **ruff ~0.14** (configured in `pyproject.toml` under `[tool.ruff]`)
- Line length: **217** (very permissive)
- Ruff rules enabled: B, C4, C9, D (docstrings), E, F, I (isort), PL, S (security), U, W, YTT
- Test files exempt from docstring rules (`D`) and `S101` (assert)
- Max McCabe complexity: 24, max branches: 35

### i18n / Localization

```bash
# Extract translatable strings
make extract_messages

# Compile message catalogs
make compile_messages
```

## Code Organization

```
src/wily/                   # Python package root (specified by tool.maturin python-source)
├── __init__.py             # Version, logger setup, format helpers
├── __main__.py             # Click CLI entry point (all subcommands defined here)
├── backend.pyi             # Type stubs for the Rust extension module
├── backend.*.pyd           # Compiled Rust extension (platform-specific)
├── cache.py                # Cache directory operations (create, clean, exists, list)
├── defaults.py             # Default constants (archiver, config path, max revisions)
├── lang.py                 # i18n/gettext support via `_()` function
├── operators.py            # Metric/Operator definitions and resolution functions
├── config/
│   ├── __init__.py         # Config loading from wily.cfg files
│   └── types.py            # WilyConfig dataclass
├── commands/
│   ├── build.py            # Build/index git history into Parquet cache
│   ├── diff.py             # Compare uncommitted files against cached metrics
│   ├── graph.py            # Generate Plotly HTML graphs of metrics over time
│   ├── index.py            # Show cache revision history
│   ├── list_metrics.py     # List available metrics
│   ├── rank.py             # Rank files by a metric
│   └── report.py           # Show metric history for a specific file
├── archivers/
│   ├── __init__.py         # BaseArchiver, Archiver, Revision types
│   ├── git.py              # Git archiver (uses Rust backend for git ops)
│   └── filesystem.py       # Filesystem archiver (non-git)
├── helper/
│   ├── __init__.py         # print_table (Rich), generate_cache_path
│   └── custom_enums.py     # ReportFormat enum
├── templates/              # HTML report templates
└── locales/                # gettext translation files (en, en_AU, de, ja)

backend/                    # Rust crate (PyO3 extension module)
├── Cargo.toml              # Rust dependencies (pyo3, ruff_python_parser, arrow, parquet, git2)
├── src/
│   ├── lib.rs              # PyO3 module registration
│   ├── storage.rs          # WilyIndex: Parquet read/write, analyze_revision, analyze_files
│   ├── git.rs              # Git operations (get_revisions, checkout, find_revision)
│   ├── files.rs            # File iteration (iter_filenames)
│   ├── raw.rs              # Raw line count metrics
│   ├── cyclomatic.rs       # Cyclomatic complexity computation
│   ├── halstead.rs         # Halstead metrics computation
│   └── maintainability.rs  # Maintainability index computation
└── benches/                # Criterion benchmarks
    └── analyze_revision/

test/
├── conftest.py             # Shared fixtures (gitdir, builddir, cache_path)
├── unit/                   # Unit tests for individual modules
└── integration/            # CLI integration tests using CliRunner
```

## Key Architecture Concepts

### The Rust Backend (`wily.backend`)

The `wily.backend` module is a compiled Rust extension (PyO3/maturin). It provides:

- **`WilyIndex`**: Context manager for reading/writing Parquet metric files. Supports `__getitem__` (lookup by path), `__iter__`, `__len__`. Writes are batched and flushed on `__exit__`.
- **`analyze_revision()`**: Parses Python files, computes all metrics (raw, cyclomatic, halstead, maintainability), stores rows in the index.
- **`analyze_files()`**: Same analysis but returns results without storing (used by `diff` command).
- **`get_revisions()`**, **`checkout_revision()`**, **`checkout_branch()`**, **`find_revision()`**: Git operations using `git2`.
- **`iter_filenames()`**: Walks directories to find `.py` files.

Type stubs are in `src/wily/backend.pyi`. When modifying the Rust API, update the `.pyi` file.

### Operators and Metrics

Operators are defined in `src/wily/operators.py`. Each operator (cyclomatic, raw, maintainability, halstead) has associated `Metric` objects with:
- `name`: Key used in storage/lookup (e.g., `"loc"`, `"complexity"`, `"mi"`)
- `metric_type`: Python type (int, float, str)
- `measure`: `MetricType.AimLow`, `AimHigh`, or `Informational` — determines color styling in output

Metrics are referenced as `operator.metric` strings (e.g., `"raw.loc"`, `"cyclomatic.complexity"`, `"maintainability.mi"`).

### Storage Format

Metrics are stored in **Parquet files** at `~/.wily/<hash>/<archiver>/metrics.parquet`. Each row represents one file's metrics for one revision. Columns include metadata (revision, date, author, message, path, path_type) and all metric values.

Row types by `path_type`:
- `"file"` — individual Python file metrics
- `"directory"` — aggregated metrics for a directory
- `"root"` — aggregated metrics for the entire project (path is `""`)
- `"function"` / `"class"` — detailed object-level metrics (path format: `"file.py:object_name"`)

### CLI Structure

The CLI uses **Click** with a group command pattern. All subcommands are defined in `__main__.py` and delegate to functions in `commands/`. Commands lazily import their implementation modules to keep startup fast:

```python
from wily.commands.build import build  # noqa: PLC0415
```

### Internationalization

All user-facing strings use `_()` from `wily.lang` (gettext). When adding new CLI text, wrap it with `_()`.

## Conventions and Patterns

### Python Style

- **Docstrings**: Google/Sphinx style with `:param:` and `:return:` tags (enforced by ruff `D` rules)
- **Imports**: isort via ruff, `wily` is a known local folder
- **Type hints**: Used throughout, modern union syntax (`str | None` not `Optional[str]`)
- **Dataclasses**: Used for config (`WilyConfig`), diff results (`MetricDiff`, `FileDiff`), revisions
- **Enums**: Used for `MetricType`, `OperatorLevel`, `ReportFormat`
- **Output formatting**: All tables use Rich via `helper.print_table()`. Commands accept `--wrap` and `--table-style` options.
- **Logging**: Use `wily.logger` (root) or `logging.getLogger(__name__)` per module

### Rust Style

- Standard Rust 2021 edition conventions
- Uses `ruff_python_parser` (from the Ruff project) for Python AST parsing
- `rayon` for parallel file processing
- `git2` for git operations
- `arrow` + `parquet` crates for columnar storage
- Enforced by `cargo clippy -- -D warnings` and `cargo fmt --check`

### Path Handling

- File paths are normalized to **Unix-style** (`/`) throughout, even on Windows
- Paths in the Parquet index are relative to the project root
- Function/class paths use colon notation: `"src/foo.py:function_name"`
- The `config.path` is the project root; `config.targets` are the files/dirs to analyze

### Testing Patterns

- Integration tests create temporary git repos with known commits using `gitpython`
- The `gitdir` fixture creates a repo with 3 revisions of increasing complexity
- Tests invoke the CLI via `CliRunner` and assert exit codes and output
- The autouse `cache_path` fixture isolates wily's cache to a temp directory
- Use `unittest.mock.patch` for simulating errors

## Important Gotchas

1. **Rust must be compiled before tests**: Run `maturin develop` before `pytest`. The `uv sync` + `uv run pytest` workflow handles this automatically in CI.

2. **Backend stubs**: The `.pyi` file (`src/wily/backend.pyi`) must be kept in sync with the Rust module's Python interface. It's the only source of type information for the backend.

3. **Maintainability depends on Raw**: `resolve_operators()` automatically adds the `raw` operator if `maintainability` is requested, because MI calculation uses LOC/SLOC/comments metrics.

4. **Parquet writes are batched**: `WilyIndex` accumulates rows in memory and writes to Parquet only on context manager exit (`__exit__`). Always use it as a context manager.

5. **Git checkout during build**: The build command checks out each historical revision to analyze it. It always calls `archiver.finish()` to restore the original branch, even on failure.

6. **Dirty repo check**: `wily build` refuses to run on a dirty git repo (uncommitted changes). This is checked in `GitArchiver.revisions()`.

7. **Diff compares uncommitted vs indexed**: The `diff` command analyzes the current working tree files and compares against the last indexed revision in the cache. It does NOT compare two indexed revisions.

8. **Lazy command imports**: Commands in `__main__.py` import their implementation inside the function body to keep `wily --help` fast. Don't move these to top-level.

9. **Pre-built `.pyd` files**: The repo contains pre-built Windows ARM64 `.pyd` files for Python 3.13 and 3.14. These are platform-specific compiled extensions.

10. **`ruff_python_parser` from git**: The Rust backend depends on `ruff_python_parser` directly from the Ruff GitHub repo's main branch (not a released crate). This can break if Ruff's API changes.

## CI

CI is defined in `.github/workflows/ci.yml` and runs on push to `master`/`v2` and PRs:

- **test**: Matrix of Python 3.10-3.14 × Linux/Windows/macOS. Installs Rust + uv, runs `uv sync --all-groups && uv run pytest`
- **ruff**: Python linting with `uv tool run ruff check .`
- **clippy**: Rust linting with `cargo clippy --manifest-path backend/Cargo.toml -- -D warnings`
- **rustfmt**: Rust formatting with `cargo fmt --manifest-path backend/Cargo.toml --check`
- **build-sdist**: Source distribution via maturin
- **build**: Platform wheels for Linux (x86_64, aarch64), macOS (x86_64, aarch64), Windows (x86_64, aarch64)

## Dependencies

### Python (runtime)
- `gitpython` — git repo validation and dirty checks
- `click` — CLI framework
- `nbformat` — Jupyter notebook support
- `plotly` — HTML graph generation
- `rich` — Terminal tables and logging

### Python (dev/test)
- `pytest`, `pytest-cov` — testing
- `radon` — reference implementation for validation
- `ruff` — linting
- `maturin` — Rust-Python build tool
- `codespell` — spell checking

### Rust
- `pyo3` — Python-Rust bindings
- `ruff_python_parser`, `ruff_python_ast` — Python parsing (from Ruff repo)
- `git2` — Git operations
- `arrow`, `parquet` — Columnar storage
- `rayon` — Parallel processing
- `walkdir` — Directory traversal
- `criterion` — Benchmarking (dev)
