//! Parallel file analysis using rayon.
//!
//! This module provides efficient parallel processing of Python files,
//! replacing Python's multiprocessing.Pool with Rust's rayon thread pool.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;

use crate::cyclomatic;
use crate::halstead;
use crate::maintainability;
use crate::raw;

/// Result of analyzing a single file with all operators.
#[derive(Debug)]
struct FileAnalysis {
    path: String,
    raw: Option<HashMap<String, i64>>,
    cyclomatic: Option<Vec<(String, i64)>>,
    halstead: Option<Vec<(String, HashMap<String, f64>)>>,
    maintainability: Option<(f64, String)>,
    error: Option<String>,
}

/// Analyze a single file with all requested operators.
fn analyze_file(
    path: &str,
    include_raw: bool,
    include_cyclomatic: bool,
    include_halstead: bool,
    include_maintainability: bool,
    multi: bool,
) -> FileAnalysis {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            return FileAnalysis {
                path: path.to_string(),
                raw: None,
                cyclomatic: None,
                halstead: None,
                maintainability: None,
                error: Some(format!("Failed to read file: {}", e)),
            };
        }
    };

    let mut result = FileAnalysis {
        path: path.to_string(),
        raw: None,
        cyclomatic: None,
        halstead: None,
        maintainability: None,
        error: None,
    };

    if include_raw {
        result.raw = Some(raw::analyze_source_raw(&source));
    }

    if include_cyclomatic {
        result.cyclomatic = Some(cyclomatic::analyze_source_cc(&source));
    }

    if include_halstead {
        result.halstead = Some(halstead::analyze_source_halstead(&source));
    }

    if include_maintainability {
        result.maintainability = Some(maintainability::analyze_source_mi(&source, multi));
    }

    result
}

/// Analyze multiple files in parallel using rayon.
///
/// This function replaces Python's multiprocessing.Pool with Rust's rayon
/// thread pool, which is more efficient for CPU-bound tasks.
///
/// # Arguments
/// * `paths` - List of file paths to analyze
/// * `operators` - List of operator names to run ("raw", "cyclomatic", "halstead", "maintainability")
/// * `multi` - Whether to include multi-line strings in MI calculation
///
/// # Returns
/// A dictionary mapping file paths to their analysis results.
#[pyfunction]
#[pyo3(signature = (paths, operators, multi=true))]
#[allow(deprecated)]
pub fn analyze_files_parallel<'py>(
    py: Python<'py>,
    paths: Vec<String>,
    operators: Vec<String>,
    multi: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let include_raw = operators.iter().any(|o| o == "raw");
    let include_cyclomatic = operators.iter().any(|o| o == "cyclomatic");
    let include_halstead = operators.iter().any(|o| o == "halstead");
    let include_maintainability = operators.iter().any(|o| o == "maintainability");

    // Release the GIL during parallel processing
    let results: Vec<FileAnalysis> = py.allow_threads(|| {
        paths
            .par_iter()
            .map(|path| {
                analyze_file(
                    path,
                    include_raw,
                    include_cyclomatic,
                    include_halstead,
                    include_maintainability,
                    multi,
                )
            })
            .collect()
    });

    // Convert results to Python dict
    let output = PyDict::new(py);

    for analysis in results {
        let file_dict = PyDict::new(py);

        if let Some(error) = analysis.error {
            file_dict.set_item("error", error)?;
            output.set_item(&analysis.path, file_dict)?;
            continue;
        }

        // Raw metrics
        if let Some(raw_metrics) = analysis.raw {
            let raw_dict = PyDict::new(py);
            let total_dict = PyDict::new(py);
            for (key, value) in raw_metrics {
                total_dict.set_item(key, value)?;
            }
            raw_dict.set_item("total", total_dict)?;
            file_dict.set_item("raw", raw_dict)?;
        }

        // Cyclomatic complexity
        if let Some(cc_results) = analysis.cyclomatic {
            let cc_dict = PyDict::new(py);
            let total_dict = PyDict::new(py);
            let mut total_complexity: i64 = 0;

            for (name, complexity) in &cc_results {
                let func_dict = PyDict::new(py);
                func_dict.set_item("complexity", *complexity)?;
                cc_dict.set_item(name.as_str(), func_dict)?;
                total_complexity += complexity;
            }

            total_dict.set_item("complexity", total_complexity)?;
            cc_dict.set_item("total", total_dict)?;
            file_dict.set_item("cyclomatic", cc_dict)?;
        }

        // Halstead metrics
        if let Some(hal_results) = analysis.halstead {
            let hal_dict = PyDict::new(py);
            let mut total_h1: i64 = 0;
            let mut total_h2: i64 = 0;
            let mut total_n1: i64 = 0;
            let mut total_n2: i64 = 0;
            let mut total_volume: f64 = 0.0;
            let mut total_difficulty: f64 = 0.0;
            let mut total_effort: f64 = 0.0;

            for (name, metrics) in &hal_results {
                let func_dict = PyDict::new(py);
                for (key, value) in metrics {
                    func_dict.set_item(key.as_str(), *value)?;
                    match key.as_str() {
                        "h1" => total_h1 += *value as i64,
                        "h2" => total_h2 += *value as i64,
                        "N1" => total_n1 += *value as i64,
                        "N2" => total_n2 += *value as i64,
                        "volume" => total_volume += *value,
                        "difficulty" => total_difficulty += *value,
                        "effort" => total_effort += *value,
                        _ => {}
                    }
                }
                hal_dict.set_item(name.as_str(), func_dict)?;
            }

            let total_dict = PyDict::new(py);
            total_dict.set_item("h1", total_h1)?;
            total_dict.set_item("h2", total_h2)?;
            total_dict.set_item("N1", total_n1)?;
            total_dict.set_item("N2", total_n2)?;
            total_dict.set_item("volume", total_volume)?;
            total_dict.set_item("difficulty", total_difficulty)?;
            total_dict.set_item("effort", total_effort)?;
            hal_dict.set_item("total", total_dict)?;
            file_dict.set_item("halstead", hal_dict)?;
        }

        // Maintainability Index
        if let Some((mi, rank)) = analysis.maintainability {
            let mi_dict = PyDict::new(py);
            let total_dict = PyDict::new(py);
            total_dict.set_item("mi", mi)?;
            total_dict.set_item("rank", rank)?;
            mi_dict.set_item("total", total_dict)?;
            file_dict.set_item("maintainability", mi_dict)?;
        }

        output.set_item(&analysis.path, file_dict)?;
    }

    Ok(output)
}

/// Register the parallel module with the Python module.
pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(analyze_files_parallel, parent_module)?)?;
    Ok(())
}
