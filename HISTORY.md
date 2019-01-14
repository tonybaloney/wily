# Release History

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
