# wily
A Python application for tracking, reporting on timing and complexity in tests and applications.

```
wily [a]:
quick to think of things, having a very good understanding of situations and possibilities, 
and often willing to use tricks to achieve an aim.
```

Wily uses git to go through each revision (commit) in a branch and run complexity and code-analysis metrics over the code. You can use this to limit your code or report on trends for complexity, length etc.

## Usage

Wily can be used via a command line interface, `wily`.

```console
 $ wily --help
 
 ```

### Configuration

You can put a `wily.cfg` file in your project directory and `wily` will override the runtime settings. Here are the available options:

```ini
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

### Command line usage

#### `wily build`

The first step to using `wily` is to build a wily cache with all of the statistics of your project. 

```
Usage: wily build [OPTIONS]

  Build the wily cache

Options:
  -h, --max-revisions INTEGER  The maximum number of historical commits to
                               archive
  -p, --path PATH              Root path to the project folder to scan
  -t, --target PATH            Subdirectories or files to scan
  -o, --operators TEXT         List of operators, seperated by commas
  --help                       Show this message and exit.
```

By default, wily will assume your project folder is a `git` directory. Wily will not build a cache if the working copy is dirty (has changed files not commited).

```console
 $ wily build
 ```
 
For a specific directory

```console
 $ wily build -p path/to/folder
```

Limit the number of revisions (defaults to 50).

```console
 $ wily build --max-revisions=10                       
Found 10 revisions from 'git' archiver in ..
Running operators - cyclomatic,raw,maintainability
Processing |################################| 30/30
Completed building wily history, run `wily report` or `wily show` to see more.
```
 
#### `wily index`

Show information about the build directory. Requires that `.wily/` exists.

```
Usage: wily index [OPTIONS]

  Show the history archive in the .wily/ folder.

Options:
  --help  Show this message and exit.
```

`wily index` will print the configuration to the screen and list all revisions that have been analysed and the operators used.

```console
 $ wily index
--------Configuration---------
Path: .
Archiver: git
Operators: {'cyclomatic', 'raw', 'maintainability'}

-----------History------------
╒══════════════════════════════════════════╤══════════════╤════════════╕
│ Revision                                 │ Author       │ Date       │
╞══════════════════════════════════════════╪══════════════╪════════════╡
│ e8110e550ed018738e9c4e2e573cd2bdc2402ad0 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ d639f1d274cf16d92f74c38fc6cfbee9fa4872bb │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 3e8af55e0f0300013fb621fe93628173907b263e │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 86484e5c33fe11d930be05e9d727846af106af34 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 3cfe33daa87cb28f0b89c1fd84e1d2c42d7613e9 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 14e31c613f094c24171e0be3448a8543e73db996 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 267b91abefb8b47a7bbed7d08889644ced691774 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 98a95a28e4753a3b783788a2208994b69d4f6b99 │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 8d8da4e1e3fdf0642693ca104d5e4b33ce0b5fad │ Anthony Shaw │ 2018-10-15 │
├──────────────────────────────────────────┼──────────────┼────────────┤
│ 7ac596ee04c2cc86b0f3aa8d7159535834befd59 │ Anthony Shaw │ 2018-10-15 │
╘══════════════════════════════════════════╧══════════════╧════════════╛
 ```
 
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

#### `wily report`

Show a specific metric for a given file, requires that `.wily/` exists

```
Usage: wily report [OPTIONS] FILE METRIC

  Show a specific metric for a given file.

Options:
  --help  Show this message and exit.
```

`wily report` will print the metric and the delta between each revision.

```console
 $ wily report wily/__main__.py raw.loc
-----------History for raw.loc------------
╒══════════════════════════════════════════╤══════════════╤════════════╤═════════════════╕
│ Revision                                 │ Author       │ Date       │ Lines of Code   │
╞══════════════════════════════════════════╪══════════════╪════════════╪═════════════════╡
│ e8110e550ed018738e9c4e2e573cd2bdc2402ad0 │ Anthony Shaw │ 2018-10-15 │ 163 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ d639f1d274cf16d92f74c38fc6cfbee9fa4872bb │ Anthony Shaw │ 2018-10-15 │ 163 (+21)       │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 3e8af55e0f0300013fb621fe93628173907b263e │ Anthony Shaw │ 2018-10-15 │ 142 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 86484e5c33fe11d930be05e9d727846af106af34 │ Anthony Shaw │ 2018-10-15 │ 142 (+14)       │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 3cfe33daa87cb28f0b89c1fd84e1d2c42d7613e9 │ Anthony Shaw │ 2018-10-15 │ 128 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 14e31c613f094c24171e0be3448a8543e73db996 │ Anthony Shaw │ 2018-10-15 │ 128 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 267b91abefb8b47a7bbed7d08889644ced691774 │ Anthony Shaw │ 2018-10-15 │ 128 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 98a95a28e4753a3b783788a2208994b69d4f6b99 │ Anthony Shaw │ 2018-10-15 │ 128 (+21)       │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 8d8da4e1e3fdf0642693ca104d5e4b33ce0b5fad │ Anthony Shaw │ 2018-10-15 │ 107 (0)         │
├──────────────────────────────────────────┼──────────────┼────────────┼─────────────────┤
│ 7ac596ee04c2cc86b0f3aa8d7159535834befd59 │ Anthony Shaw │ 2018-10-15 │ 107 (0)         │
╘══════════════════════════════════════════╧══════════════╧════════════╧═════════════════╛

```

#### `wily graph`

Similar to `wily report` but instead of printing in the console, `wily` will print a graph in a browser.
