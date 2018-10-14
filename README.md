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
 $ wily build --max-revisions=20
 ```
 
#### `wily show`

Show information about the build directory. Requires that `.wily/` exists.

`wily show` will print the configuration to the screen and list all revisions that have been analysed and the operators used.

```console
 $ wily show
--------Configuration---------
Path: .
Archiver: git
Operators: {'raw', 'cyclomatic', 'maintainability'}

-----------History------------
Revision                                  Author        Operators
----------------------------------------  ------------  --------------------------------
213868438ff348867d830da9736d93007e6384ac  Anthony Shaw  cyclomatic, raw, maintainability
6934eda7e36b975062192bfe08e8b3cc054465fd  Anthony Shaw  cyclomatic, raw, maintainability
 ```