//! File iteration utilities for discovering Python source files.
//!
//! This module provides a Rust implementation of radon's `iter_filenames` function,
//! which discovers Python files in directories while respecting exclude and ignore patterns.

use glob::Pattern;
use pyo3::prelude::*;
use std::path::Path;
use walkdir::WalkDir;

/// Check if a file is a Python source file.
///
/// A file is considered a Python file if:
/// - It ends with `.py`
/// - It ends with `.ipynb` (if include_ipynb is true)
pub fn is_python_file(path: &Path, include_ipynb: bool) -> bool {
    let filename = match path.file_name() {
        Some(name) => name.to_string_lossy(),
        _ => return false,
    };

    return is_python_filename(&filename, include_ipynb);
}

pub fn is_python_filename(filename: &str, include_ipynb: bool) -> bool {
    if filename.ends_with(".py") {
        return true;
    }

    if include_ipynb && filename.ends_with(".ipynb") {
        return true;
    }
    false
}

/// Check if a path matches any of the given glob patterns.
fn matches_any_pattern(path: &str, patterns: &[Pattern]) -> bool {
    patterns.iter().any(|p| p.matches(path))
}

/// Parse a comma-separated string of patterns into glob patterns.
/// For exclude patterns, these are fnmatch-style patterns.
fn parse_exclude_patterns(exclude: Option<&str>) -> Vec<Pattern> {
    match exclude {
        Some(s) if !s.is_empty() => s
            .split(',')
            .filter_map(|p| {
                let trimmed = p.trim();
                if trimmed.is_empty() {
                    None
                } else {
                    Pattern::new(trimmed).ok()
                }
            })
            .collect(),
        _ => Vec::new(),
    }
}

/// Parse a comma-separated string of directory names to ignore.
/// Always includes ".*" (hidden directories) by default.
fn parse_ignore_patterns(ignore: Option<&str>) -> Vec<Pattern> {
    let mut patterns = vec![Pattern::new(".*").unwrap()];

    if let Some(s) = ignore {
        if !s.is_empty() {
            for p in s.split(',') {
                let trimmed = p.trim();
                if !trimmed.is_empty() {
                    if let Ok(pattern) = Pattern::new(trimmed) {
                        patterns.push(pattern);
                    }
                }
            }
        }
    }

    patterns
}

/// Check if a directory name should be ignored.
fn should_ignore_dir(dir_name: &str, ignore_patterns: &[Pattern]) -> bool {
    matches_any_pattern(dir_name, ignore_patterns)
}

/// Check if a file path should be excluded.
fn should_exclude_file(path: &str, exclude_patterns: &[Pattern]) -> bool {
    matches_any_pattern(path, exclude_patterns)
}

/// Iterate over Python files in the given paths.
///
/// # Arguments
/// * `paths` - List of file or directory paths to search
/// * `exclude` - Comma-separated glob patterns for files to exclude
/// * `ignore` - Comma-separated directory names to ignore (hidden dirs always ignored)
/// * `include_ipynb` - Whether to include Jupyter notebook files
///
/// # Returns
/// A list of absolute paths to Python files found.
#[pyfunction]
#[pyo3(signature = (paths, exclude=None, ignore=None, include_ipynb=true))]
pub fn iter_filenames(
    paths: Vec<String>,
    exclude: Option<&str>,
    ignore: Option<&str>,
    include_ipynb: bool,
) -> PyResult<Vec<String>> {
    let exclude_patterns = parse_exclude_patterns(exclude);
    let ignore_patterns = parse_ignore_patterns(ignore);

    let mut results = Vec::new();

    for path_str in paths {
        let path = Path::new(&path_str);

        if path.is_file() {
            // Single file - check if it's Python and not excluded
            if is_python_file(path, include_ipynb) {
                let normalized = path
                    .canonicalize()
                    .unwrap_or_else(|_| path.to_path_buf())
                    .to_string_lossy()
                    .to_string();

                // Strip \\?\ prefix on Windows and normalize to Unix-style paths
                let normalized = normalized.strip_prefix(r"\\?\").unwrap_or(&normalized);
                let normalized = normalized.replace('\\', "/");

                if !should_exclude_file(&normalized, &exclude_patterns)
                    && !should_exclude_file(&path_str, &exclude_patterns)
                {
                    results.push(normalized);
                }
            }
        } else if path.is_dir() {
            // Directory - walk recursively
            for entry in WalkDir::new(path).into_iter().filter_entry(|e| {
                // Filter out ignored directories
                if e.file_type().is_dir() {
                    let dir_name = e.file_name().to_string_lossy();
                    !should_ignore_dir(&dir_name, &ignore_patterns)
                } else {
                    true
                }
            }) {
                match entry {
                    Ok(entry) => {
                        let entry_path = entry.path();

                        // Skip directories themselves
                        if entry_path.is_dir() {
                            continue;
                        }

                        // Skip hidden files
                        if let Some(name) = entry_path.file_name() {
                            if name.to_string_lossy().starts_with('.') {
                                continue;
                            }
                        }

                        // Check if it's a Python file
                        if !is_python_file(entry_path, include_ipynb) {
                            continue;
                        }

                        let normalized = entry_path
                            .canonicalize()
                            .unwrap_or_else(|_| entry_path.to_path_buf())
                            .to_string_lossy()
                            .to_string();

                        // Strip \\?\ prefix on Windows and normalize to Unix-style paths
                        let normalized = normalized.strip_prefix(r"\\?\").unwrap_or(&normalized);
                        let normalized = normalized.replace('\\', "/");

                        // Check exclude patterns against both original and normalized path
                        let entry_str = entry_path.to_string_lossy();
                        if !should_exclude_file(&normalized, &exclude_patterns)
                            && !should_exclude_file(&entry_str, &exclude_patterns)
                        {
                            results.push(normalized);
                        }
                    }
                    Err(_) => continue,
                }
            }
        }
    }

    Ok(results)
}

/// Register the files module with the Python module.
pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(iter_filenames, parent_module)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_exclude_patterns() {
        let patterns = parse_exclude_patterns(Some("*.pyc,__pycache__/*"));
        assert_eq!(patterns.len(), 2);
    }

    #[test]
    fn test_parse_ignore_patterns() {
        let patterns = parse_ignore_patterns(Some("venv,node_modules"));
        // Should have 3: .*, venv, node_modules
        assert_eq!(patterns.len(), 3);
    }

    #[test]
    fn test_parse_ignore_patterns_default() {
        let patterns = parse_ignore_patterns(None);
        // Should have just .*
        assert_eq!(patterns.len(), 1);
    }

    #[test]
    fn test_matches_pattern() {
        let patterns = vec![Pattern::new("*.pyc").unwrap()];
        assert!(matches_any_pattern("test.pyc", &patterns));
        assert!(!matches_any_pattern("test.py", &patterns));
    }
}
