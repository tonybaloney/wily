============================
Migrating from v1 to v2
============================

Wily v2 is a major rewrite. The analysis backend has been replaced with a Rust native extension, the storage format has changed from JSON to Parquet, and several operators have been renamed or replaced. This guide covers everything you need to know to upgrade.

.. contents:: On this page
   :local:
   :depth: 2

Requirements
------------

- **Python 3.10+** is required. Wily v1 supported Python 3.6+.
- **Rust toolchain** is only needed if building from source. Pre-built wheels are available for Linux, macOS, and Windows (x86_64 and aarch64).

Rebuilding the cache
--------------------

The v1 cache (JSON files under ``~/.wily/``) is **not compatible** with v2. You must rebuild:

.. code-block:: console

   $ wily clean -y
   $ wily build src/

This will delete the old cache and create a new one using the Parquet storage format. The new cache is significantly faster for large codebases thanks to columnar storage and parallel analysis.

.. note::

   If you use ``--cache`` to specify a custom cache path, make sure to clean and rebuild that location as well.

Operator and metric changes
---------------------------

Removed: ``mccabe``
~~~~~~~~~~~~~~~~~~~~

The ``mccabe`` operator from v1 (which used the ``mccabe`` Python package) has been **removed**. Its functionality is replaced by the ``cyclomatic`` operator, which now uses Ruff's AST parser implemented in Rust.

If you referenced ``mccabe`` in your configuration or scripts, change it to ``cyclomatic``:

.. code-block:: console

   # v1
   $ wily build src/ -o raw,mccabe,maintainability

   # v2
   $ wily build src/ -o raw,cyclomatic,maintainability

The metric name remains ``complexity`` (accessed as ``cyclomatic.complexity``), so ``wily report`` and ``wily graph`` commands using that metric name will continue to work.

New: ``cognitive``
~~~~~~~~~~~~~~~~~~

v2 adds a new ``cognitive`` operator that measures cognitive complexity — how hard code is to *understand*, as opposed to cyclomatic complexity which measures structural/branching complexity. Based on the SonarSource "Cognitive Complexity" paper by G. Ann Campbell (2017).

.. code-block:: console

   $ wily build src/ -o raw,cyclomatic,cognitive,maintainability
   $ wily report src/module.py cognitive.cognitive_complexity

Default operators
~~~~~~~~~~~~~~~~~

In v2, the default operator set is: ``cyclomatic``, ``maintainability``, ``raw``, ``halstead``, and ``cognitive``. In v1, the defaults were: ``raw``, ``maintainability``, ``cyclomatic``, and ``halstead``.

The main difference is that ``cognitive`` is now included by default.

Metric name reference
~~~~~~~~~~~~~~~~~~~~~

All metrics from v1 are still available in v2 under the same names. Here is the complete list:

.. list-table:: Metrics
   :header-rows: 1
   :widths: 25 35 15

   * - Metric key
     - Description
     - Operator
   * - ``raw.loc``
     - Lines of Code
     - raw
   * - ``raw.lloc``
     - Logical Lines of Code
     - raw
   * - ``raw.sloc``
     - Source Lines of Code
     - raw
   * - ``raw.comments``
     - Multi-line comments
     - raw
   * - ``raw.multi``
     - Multi lines
     - raw
   * - ``raw.blank``
     - Blank lines
     - raw
   * - ``raw.single_comments``
     - Single comment lines
     - raw
   * - ``cyclomatic.complexity``
     - Cyclomatic Complexity
     - cyclomatic
   * - ``halstead.h1``
     - Unique Operators
     - halstead
   * - ``halstead.h2``
     - Unique Operands
     - halstead
   * - ``halstead.N1``
     - Number of Operators
     - halstead
   * - ``halstead.N2``
     - Number of Operands
     - halstead
   * - ``halstead.vocabulary``
     - Unique vocabulary (h1 + h2)
     - halstead
   * - ``halstead.length``
     - Length of application
     - halstead
   * - ``halstead.volume``
     - Code volume
     - halstead
   * - ``halstead.difficulty``
     - Difficulty
     - halstead
   * - ``halstead.effort``
     - Effort
     - halstead
   * - ``maintainability.mi``
     - Maintainability Index
     - maintainability
   * - ``maintainability.rank``
     - Maintainability Ranking (A/B/C)
     - maintainability
   * - ``cognitive.cognitive_complexity``
     - Cognitive Complexity *(new in v2)*
     - cognitive

CLI changes
-----------

The CLI commands are largely the same between v1 and v2. The main differences are:

New options on existing commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several commands gained new formatting options in v2:

- ``--wrap/--no-wrap``: Control whether output wraps to terminal width (available on ``index``, ``rank``, ``report``, ``diff``, ``list-metrics``)
- ``--table-style``: Choose a Rich table border style such as ``ROUNDED``, ``ASCII``, ``SIMPLE``, ``MINIMAL``, or ``MARKDOWN`` (available on the same commands)
- ``--json/--no-json``: Output ``diff`` results in JSON format

Output formatting
~~~~~~~~~~~~~~~~~

- v1 used ``tabulate`` for console tables. v2 uses **Rich**, which provides better terminal rendering with color support and configurable table styles.
- HTML reports continue to work with the ``-f HTML`` option on ``wily report``.

Removed dependencies
--------------------

v2 removes several Python dependencies that were used in v1 for metric computation:

.. list-table:: Dependency changes
   :header-rows: 1
   :widths: 30 30

   * - v1 (Python)
     - v2 (Rust backend)
   * - ``radon`` (cyclomatic, raw, halstead, MI)
     - Built-in Rust implementation using ``ruff_python_parser``
   * - ``mccabe`` (McCabe complexity)
     - Removed (replaced by ``cyclomatic`` operator)
   * - ``tabulate`` (console output)
     - Replaced by ``rich``

The remaining Python dependencies in v2 are: ``gitpython``, ``click``, ``nbformat``, ``plotly``, and ``rich``.

Storage format
--------------

.. list-table:: Storage comparison
   :header-rows: 1
   :widths: 20 40 40

   * -
     - v1
     - v2
   * - Format
     - JSON files (one per revision per operator)
     - Single Parquet file per archiver
   * - Location
     - ``~/.wily/<hash>/<archiver>/<revision>.json``
     - ``~/.wily/<hash>/<archiver>/metrics.parquet``
   * - Schema
     - Nested JSON (operator → path → metrics)
     - Flat columnar (one row per file per revision)
   * - Performance
     - Slower on large codebases
     - Significantly faster (columnar reads + parallel writes)

The Parquet schema stores metadata columns (``revision``, ``date``, ``author``, ``message``, ``path``, ``path_type``) alongside all metric values as top-level columns.

Row types by ``path_type``:

- ``"file"`` — metrics for an individual Python file
- ``"directory"`` — aggregated metrics for a directory
- ``"root"`` — aggregated metrics for the entire project (path is ``""``)
- ``"function"`` / ``"class"`` — detailed object-level metrics (path format: ``"file.py:object_name"``)

Configuration
-------------

Wily v2 continues to read configuration from ``wily.cfg`` files. The configuration format is unchanged.

The ``--path``, ``--cache``, ``--debug``, and ``--config`` global options work the same as in v1.

Pre-commit hook
---------------

The pre-commit hook configuration is unchanged:

.. code-block:: yaml

    repos:
    -   repo: local
        hooks:
        -   id: wily
            name: wily
            entry: wily diff
            verbose: true
            language: python
            additional_dependencies: [wily]

CI/CD usage
-----------

If you use wily in CI/CD pipelines:

1. **Update your Python version** to 3.10+ if not already.
2. **Remove ``mccabe`` references** from any operator lists.
3. **Rebuild your cache** — if you cache the ``~/.wily/`` directory between CI runs, delete it and rebuild. The v1 JSON cache is not compatible.
4. **Update any metric parsing scripts** — if you parse wily's output programmatically, note that the console output now uses Rich formatting. Use ``wily diff --json`` for machine-readable output.

Performance improvements
------------------------

v2 brings significant performance improvements:

- **Parallel file analysis**: Files are analyzed in parallel using Rayon (Rust). Build times are substantially faster on multi-core machines.
- **Rust-native parsing**: Python AST parsing uses ``ruff_python_parser`` (from the Ruff project), which is much faster than the Python-based ``radon`` and ``mccabe`` packages.
- **Columnar storage**: Parquet format enables faster reads for report and graph operations, especially on large indexes.
- **Reduced Python overhead**: The hot path (parsing, metric computation, storage I/O) runs entirely in Rust.

Quick migration checklist
-------------------------

1. ✅ Ensure Python 3.10+ is installed
2. ✅ Install wily v2: ``pip install wily``
3. ✅ Delete old cache: ``wily clean -y``
4. ✅ Replace ``mccabe`` with ``cyclomatic`` in any config or scripts
5. ✅ Rebuild the index: ``wily build src/``
6. ✅ Verify with ``wily report`` or ``wily index``
7. ✅ Optionally try the new ``cognitive`` operator
