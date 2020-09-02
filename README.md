![wily](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/logo.png)

A command-line application for tracking, reporting on complexity of Python tests and applications.

[![Wily](https://img.shields.io/badge/%F0%9F%A6%8A%20wily-passing-brightgreen.svg)](https://wily.readthedocs.io/)
[![Build Status](https://dev.azure.com/AnthonyShaw/wily/_apis/build/status/tonybaloney.wily?branchName=master)](https://dev.azure.com/AnthonyShaw/wily/_build/latest?definitionId=1&branchName=master)
[![codecov](https://codecov.io/gh/tonybaloney/wily/branch/master/graph/badge.svg)](https://codecov.io/gh/tonybaloney/wily) [![Documentation Status](https://readthedocs.org/projects/wily/badge/?version=latest)](https://wily.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/wily.svg)](https://badge.fury.io/py/wily) ![black](https://img.shields.io/badge/code%20style-black-000000.svg)


```
wily [a]:
quick to think of things, having a very good understanding of situations and possibilities, 
and often willing to use tricks to achieve an aim.
```

Wily uses git to go through each revision (commit) in a branch and run complexity and code-analysis metrics over the code. You can use this to limit your code or report on trends for complexity, length etc.

## Installation

Wily can be installed via pip from Python 3.6 and above:

```console
 $ pip install wily
```

## Usage

See the [Documentation Site](https://wily.readthedocs.io/) for full usage guides.

Wily can be used via a command line interface, `wily`.

```console
 $ wily --help
```

![help-screen](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/wily_help.png)

## Demo

Here is a demo of wily analysing a Python project, giving a summary of changes to complexity in the last 10 commits and then showing changes against a specific git revision: 

![demo](./docs/source/_static/termtosvg_leo0ur6s.svg)

## Using Wily in a CI/CD pipeline

Wily can be used in a CI/CD workflow to compare the complexity of the current files against a particular revision.

By default wily will compare against the previous revision (for a git-pre-commit hook) but you can also give a Git ref, for example `HEAD^1` is the commit before the HEAD reference.

```console
 $ wily build src/
 $ wily diff src/ -r HEAD^1
```

Or, to compare against

```console
 $ wily build src/
 $ wily diff src/ -r master
```

## pre-commit plugin

You can install wily as a [pre-commit](http://www.pre-commit.com/) plugin by adding the following to ``.pre-commit-config.yaml``

```yaml
repos:
-   repo: local
    hooks:
    -   id: wily
        name: wily
        entry: wily diff
        verbose: true
        language: python
        additional_dependencies: [wily]
```

### Command line usage

#### `wily build`

The first step to using `wily` is to build a wily cache with the statistics of your project. 

```
Usage: __main__.py build [OPTIONS] [TARGETS]...

  Build the wily cache

Options:
  -n, --max-revisions INTEGER  The maximum number of historical commits to
                               archive
  -o, --operators TEXT         List of operators, separated by commas
  --help                       Show this message and exit.
```

By default, wily will assume your project folder is a `git` directory. Wily will not build a cache if the working copy is dirty (has changed files not committed).

```console
 $ wily build src/
 ```

Limit the number of revisions (defaults to 50).

![wily-build](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/wily_build.png)


#### `wily report`

Show a specific metric for a given file, requires that `.wily/` exists

`wily report` will print the metric and the delta between each revision.

![wily-report](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/wily_report.png)

#### `wily rank`

Show the ranking for all files in a directory or a single file based on the metric provided, requires that `.wily/` exists

`wily rank` will print a table of files and their metric values.

![wily-rank](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/wily_rank.png)

#### `wily graph`

Similar to `wily report` but instead of printing in the console, `wily` will print a graph in a browser.

![wily-graph](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/single_metric_graph.png)

#### `wily index`

Show information about the build directory. Requires that `.wily/` exists.

`wily index` will print the configuration to the screen and list all revisions that have been analysed and the operators used.

![wily-graph](https://github.com/tonybaloney/wily/raw/master/docs/source/_static/wily_index.png)

 
### `wily list-metrics`

List the metrics available in the Wily operators. Each one of the metrics can be used in `wily graph` and `wily report`

```console
 $ wily list-metrics
mccabe operator:
No metrics available
raw operator:
╒═════════════════╤══════════════════════╤═══════════════╤══════════════════════════╕
│                 │ Name                 │ Description   │ Type                     │
╞═════════════════╪══════════════════════╪═══════════════╪══════════════════════════╡
│ loc             │ Lines of Code        │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ lloc            │ L Lines of Code      │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ sloc            │ S Lines of Code      │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ comments        │ Multi-line comments  │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ multi           │ Multi lines          │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ blank           │ blank lines          │ <class 'int'> │ MetricType.Informational │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┤
│ single_comments │ Single comment lines │ <class 'int'> │ MetricType.Informational │
╘═════════════════╧══════════════════════╧═══════════════╧══════════════════════════╛
cyclomatic operator:
No metrics available
maintainability operator:
╒══════╤═════════════════════════╤═════════════════╤══════════════════════════╕
│      │ Name                    │ Description     │ Type                     │
╞══════╪═════════════════════════╪═════════════════╪══════════════════════════╡
│ rank │ Maintainability Ranking │ <class 'str'>   │ MetricType.Informational │
├──────┼─────────────────────────┼─────────────────┼──────────────────────────┤
│ mi   │ Maintainability Index   │ <class 'float'> │ MetricType.AimLow        │
╘══════╧═════════════════════════╧═════════════════╧══════════════════════════╛
```

## Configuration

You can put a `wily.cfg` file in your project directory and `wily` will override the runtime settings. Here are the available options:

```ini
[wily]
# list of operators, choose from cyclomatic, maintainability, mccabe and raw
operators = cyclomatic,raw
# archiver to use, defaults to git
archiver = git
# path to analyse, defaults to .
path = /path/to/target
# max revisions to archive, defaults to 50
max_revisions = 20
```

You can also override the path to the configuration with the `--config` flag on the command-line.

## IPython/Jupyter Notebooks

Wily will detect and scan all Python code in .ipynb files automatically. 

You can disable this behaviour if you require by setting `ipynb_support = false` in the configuration.
You can also disable the behaviour of reporting on individual cells by setting `ipynb_cells = false`.


# Credits

## Contributors

- @wcooley (Wil Cooley)
- @DahlitzFlorian (Florian Dahlitz)
- @alegonz
- @DanielChabrowski
- @jwattier

"cute animal doing dabbing" [Designed by Freepik](https://www.freepik.com/free-vector/cute-animal-doing-dabbing_2462508.htm)
