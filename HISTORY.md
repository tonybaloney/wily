# Release History

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