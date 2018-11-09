# Release History

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