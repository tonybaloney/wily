# Release History

## 1.19.0 (2nd September 2020)

* Added a German translation (@DahlitzFlorian)
* Added the version number to the help text (@DahlitzFlorian)

## 1.18.0 (28th August 2020)

* Added infrastructure for international languages in CLI
* Fixed bug on configuration of operators [PR#116](https://github.com/tonybaloney/wily/pull/116) by @skarzi

## 1.17.1 (20th August 2020)

* Fixed bug in use of mkstemp in log files

## 1.17.0 (20th August 2020)

* Fixed the color of the maintainability index so higher is better (green)

## 1.16.0 (12th December 2019)

* Added a `rank` command to show files either matching a pattern or all in the index sorted by a particular metric.

## 1.15.0 (9th December 2019)

* Git archiver now supports a detached head state. Means that wily build can run in a detached head, will checkout the reference after build.
* Add argument to `wily diff` to specify a target revision to compare with, can be a Git SHA or a Git reference, e.g. `HEAD^1`
* `wily diff` argument for `--all`/`--changes-only` has shorter `-a`/`-c` also.
* `wily diff` argument for `--metrics` has shorter `-m` also.
* `wily report` argument for `--message` has shorter `-m` also.
* `wily index` argument for `--message` has shorter `-m` also.
* Added examples, tests and documentation for CICD patterns.

## 1.14.1 (6th December 2019)

* Debug logs are always stored in a temporary local file, on the event of a crash, wily will suggest the user to upload this file to GitHub with a copy of the crash log
* Unhandled exceptions raised by the operators (normally file formatting) are now debug events not warnings
* Updated to flit 2.0 for packaging (development change, no impact to users)
* Moved source code to src/ (development change, no impact to users)

## 1.14.0 (6th December 2019)

* The build process uses the metadata from Git to only scan the files that have changed for each revision. Significantly speeds up build times (25x>).
* The diff process uses multiprocessing to make it 3-4x faster to complete.
* Officially add support for Python 3.8.
* Process crashes are now captured and output on the console in the debug log.
* State index building is 10-20% faster.

## 1.13.0 (29th November 2019)

* Updated radon to 4.0.0
* Added support for IPython Notebooks (enabled by default)

## 1.12.4 (22nd September 2019)

* [BUGFIX](https://github.com/tonybaloney/wily/issues/73) Fixed ``TypeError: unsupported operand type(s) for +: 'int' and 'dict'`` occurring when a file contains multiple functions with the same name.
  Fixes [73](https://github.com/tonybaloney/wily/issues/73) by @alegonz
* Updated code style to meet black requirements.

## 1.12.3 (19th July 2019

* Pinned version of radon as newer version has API changes.

## 1.12.2 (14th March 2019)

* [BUGFIX] Fixed an issue where illegal/unusual filepath characters within the git history would cause the halstead harvester to crash unrecoverably. Halstead will now handle and report the error but mark the file as missing in the index (https://github.com/tonybaloney/wily/issues/64) fixed in https://github.com/tonybaloney/wily/pull/63 by @abadger.

## 1.12.1 (3rd February 2019)

* [BUGFIX] Fixed an issue where calling a command without a wily index would run the CLI wizard prompt, but immediately crash because the --skip-git-ignore flag no longer exists (https://github.com/tonybaloney/wily/issues/61)

## 1.12.0 (25th January 2019)

* [BUGFIX] Fixed an issue where path could not be set via the configuration file because it is required in the CLI
* Metrics no longer need to be in full, e.g. 'raw.loc', but instead can simply be the name, e.g. 'loc' across all commands.

## 1.11.0 (14th January 2019)

* Added a `--console-format` option to the report command to create Markdown, rST or other formats.

## 1.10.0

* Report command now has the ability to generate HTML reports with the `-f HTML` option @DahlitzFlorian
* Halstead metrics enabled by default

## 1.9.0 (28th December 2018)

* Wily now supports Windows! Full test suite works on Windows, Mac OS and Linux
* Wily no longer puts the .wily cache in the target path, cache is now stored in the $HOME path. This means you no longer need to add .wily to .gitignore before running a build. Wily will isolate cache folders based on the absolute path
* Added a --cache flag to specify the path to the cache for shared cache's
* Added `-V` version flag and added current version to `--help` header @DahlitzFlorian

## 1.8.2 (21st December 2018)

* [BUGFIX] Fixed an issue where the aggregation of the maintainability.rank metric would cause the build to crash if 2 files in the same directory had the same rank. 

## 1.8.1 (19th Decemember 2018)

* [BUGFIX] Fixed an issue that occured if a target project contained a revision with invalid Python syntax, this is quite common, especially on long projects. The cyclomatic op would crash, also the aggregation logic would expect all metrics to be inside the output. This change avoids that and raises a warning instead.

## 1.8.0 (14th December 2018)

* Build process is now run with a multiprocess pool, build times are 50-70% faster (depending on number of operators)
* Build process will now create a stub for each directory so you can run report on any directory and it will give you aggregate metrics. Each metric specifies it's own aggregation function.

## 1.7.0 (12th December 2018)

* Add halstead metrics as an optional operator
* Add an archiver flag to the build command (`-a`)
* Add a new filesystem archiver as an alternative to the git archiver for when you want to measure changes between files without having to use git.
* Setup new workflow - if the git archiver fails to initialise, build will default to the filesystem assuming the path is not a git repository.

## 1.6.0 (30th November 2018)

**NB: Upgrade will warn about index rebuild, this is expected behaviour**

* Support for directories in graph command, will recursively scan all .py files and graph them
* Support for configuring the x-axis on the graph command (defaults to history) to a custom metric
* Support for configuring the z-axis (size of bubble on scatter) in graph command by specifying a second metric
* Set metrics to cap at 2 possible options in graph command
* Running the test suite no longer opens 12 browser windows :-)
* __API Change__ The `wily report` command now takes the metrics as the 2nd - nth arguments, instead of via ``--metrics``
* Lots more documentation! See https://wily.readthedocs.io/ 

## 1.5.0 (27th November 2018)

**NB: Changes to the wily index will require a rebuild of cache.**

* Introduce index versioning, raises a warning if index is old
* Add a `setup` command, which will be prompted by default in the absence of wily cache
* Wily `build` now specifies the maximum revisions using `-n` instead of `-h`, which was confusing with `--help`
* Build targets are now a required argument
* `skip-ignore-check` argument in build renamed to `skip-gitignore-check`
* All commands will prompt to build instead of raising an error for missing cache
* `files` is now a required argument for the diff command
* `metrics` is now a required argument for the graph command
* Fixed various bugs
* Improved performance

## 1.4.0 (16th November 2018)

* Support for cyclomatic complexity of methods, functions and classes
* Extend the report and graph command line to support querying of methods, classes and functions within a file
* Sort the index before storing by date (descending) in-case the order changes for git commits
* Diff will only show files with changed metrics by default
* Extend the diff command to have an --all flag to show all changes
* Diff command now supports granular metrics \o/
* Added lines-of-code metric to the granular metrics

## 1.3.0 (14th November 2018)

* Support multiple metrics in graph command
* Git archiver will now check for existence of '.wily/', '.wily/**/*', '.wily', and others in .gitignore
* Introduce a new `--output` flag to the graph command to specify output HTML file instead of opening file in browser.
* Added toggle for disabling the .gitignore check in git archiver
* Add an --skip-ignore-check option to `wily build` to skip the checking of .gitignore 
* Remove references to the mccabe algorithm as it's not implemented

## 1.2.0 (9th November 2018)

* Complete support for pre-commit

## 1.1.1 (9th November 2018)

* Fix a bug where .gitignore was not being passed correctly

## 1.1.0 (9th November 2018)

* Add a 'diff' command to show the metrics changed values between the last index and the current data.

## 1.0.0 (9th November 2018)

* Build now compares existing git history with the cached history and only builds the missing revisions instead of building the entire index
* Will check if .wily/ is not in .gitignore before running build
* Improved documentation..

## 0.9.0 (9th November 2018)


* The build command now requires the target path, and supports multiple paths. Is no longer -t option, but an argument. This is to prevent the user from accidentally trying to scan venv's
* Operators all have a default metric (lines-of-code, maintainability-index)
* Report command by default will now display the default metrics in an index
* Report command now accepts multiple metrics and adds them to the table

## 0.8.0 (7th November 2018)

* Add support for relative paths in cache
* Fixed bug when non-standard (ie. cwd) was used as the target, would not find items to report
* Add a dabbing fox as a logo
* Add documentation
* Add integration and unit tests for the main commands and packages
