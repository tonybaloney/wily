//! Parallel file analysis using rayon.
//!
//! This module provides efficient parallel processing of Python files,
//! replacing Python's multiprocessing.Pool with Rust's rayon thread pool.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::fs;

use crate::cyclomatic;
use crate::halstead;
use crate::maintainability;
use crate::raw;

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

    // Read all files and release GIL during parallel processing
    let file_contents: Vec<(String, Result<String, String>)> = py.allow_threads(|| {
        paths
            .par_iter()
            .map(|path| {
                let content = fs::read_to_string(path)
                    .map_err(|e| format!("Failed to read file: {}", e));
                (path.clone(), content)
            })
            .collect()
    });

    // Convert results to Python dict
    let output = PyDict::new(py);

    for (path, content_result) in file_contents {
        let file_dict = PyDict::new(py);

        let source = match content_result {
            Ok(s) => s,
            Err(e) => {
                file_dict.set_item("error", e)?;
                output.set_item(&path, file_dict)?;
                continue;
            }
        };

        // Raw metrics
        if include_raw {
            let raw_metrics = raw::analyze_source_raw(&source);
            let raw_dict = PyDict::new(py);
            let total_dict = PyDict::new(py);
            for (key, value) in raw_metrics {
                total_dict.set_item(key, value)?;
            }
            raw_dict.set_item("total", total_dict)?;
            file_dict.set_item("raw", raw_dict)?;
        }

        // Cyclomatic complexity - use harvest function format
        if include_cyclomatic {
            let cc_result = cyclomatic::analyze_source_full(&source);
            let cc_dict = PyDict::new(py);
            
            match cc_result {
                Ok((functions, classes, line_index)) => {
                    let detailed_dict = PyDict::new(py);
                    let mut total_complexity: i64 = 0;

                    // Process functions (includes methods from classes)
                    for func in &functions {
                        let func_dict = PyDict::new(py);
                        let lineno = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(func.start_offset));
                        let endline = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(func.end_offset));
                        let lineno_val = lineno.to_zero_indexed() + 1;
                        let endline_val = endline.to_zero_indexed() + 1;
                        
                        func_dict.set_item("name", &func.name)?;
                        func_dict.set_item("is_method", func.is_method)?;
                        func_dict.set_item("classname", func.classname.as_deref())?;
                        func_dict.set_item("complexity", func.complexity)?;
                        func_dict.set_item("lineno", lineno_val)?;
                        func_dict.set_item("endline", endline_val)?;
                        func_dict.set_item("loc", endline_val as i64 - lineno_val as i64)?;
                        
                        let closures_list = PyList::empty(py);
                        func_dict.set_item("closures", closures_list)?;
                        
                        let fullname = func.fullname();
                        detailed_dict.set_item(fullname.as_str(), func_dict)?;
                        total_complexity += func.complexity as i64;
                    }

                    // Process classes
                    for cls in &classes {
                        let cls_dict = PyDict::new(py);
                        let lineno = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(cls.start_offset));
                        let endline = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(cls.end_offset));
                        let lineno_val = lineno.to_zero_indexed() + 1;
                        let endline_val = endline.to_zero_indexed() + 1;
                        
                        cls_dict.set_item("name", &cls.name)?;
                        cls_dict.set_item("complexity", cls.complexity())?;
                        cls_dict.set_item("real_complexity", cls.real_complexity)?;
                        cls_dict.set_item("lineno", lineno_val)?;
                        cls_dict.set_item("endline", endline_val)?;
                        cls_dict.set_item("loc", endline_val as i64 - lineno_val as i64)?;
                        
                        let inner_classes_list = PyList::empty(py);
                        cls_dict.set_item("inner_classes", inner_classes_list)?;
                        
                        detailed_dict.set_item(cls.name.as_str(), cls_dict)?;
                        total_complexity += cls.complexity() as i64;
                    }

                    let total_dict = PyDict::new(py);
                    total_dict.set_item("complexity", total_complexity)?;
                    cc_dict.set_item("detailed", detailed_dict)?;
                    cc_dict.set_item("total", total_dict)?;
                }
                Err(_) => {
                    let detailed_dict = PyDict::new(py);
                    let total_dict = PyDict::new(py);
                    total_dict.set_item("complexity", 0)?;
                    cc_dict.set_item("detailed", detailed_dict)?;
                    cc_dict.set_item("total", total_dict)?;
                }
            }
            file_dict.set_item("cyclomatic", cc_dict)?;
        }

        // Halstead metrics
        if include_halstead {
            let hal_result = halstead::analyze_source_full(&source);
            let hal_dict = PyDict::new(py);
            
            match hal_result {
                Ok((functions, total, line_index)) => {
                    let detailed_dict = PyDict::new(py);
                    
                    for func in &functions {
                        let func_dict = PyDict::new(py);
                        let lineno = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(func.start_offset));
                        let endline = ruff_source_file::LineIndex::line_index(&line_index, ruff_text_size::TextSize::new(func.end_offset));
                        
                        func_dict.set_item("h1", func.metrics.h1())?;
                        func_dict.set_item("h2", func.metrics.h2())?;
                        func_dict.set_item("N1", func.metrics.n1())?;
                        func_dict.set_item("N2", func.metrics.n2())?;
                        func_dict.set_item("vocabulary", func.metrics.vocabulary())?;
                        func_dict.set_item("length", func.metrics.length())?;
                        func_dict.set_item("volume", func.metrics.volume())?;
                        func_dict.set_item("difficulty", func.metrics.difficulty())?;
                        func_dict.set_item("effort", func.metrics.effort())?;
                        func_dict.set_item("lineno", lineno.to_zero_indexed() + 1)?;
                        func_dict.set_item("endline", endline.to_zero_indexed() + 1)?;
                        
                        detailed_dict.set_item(func.name.as_str(), func_dict)?;
                    }
                    
                    let total_dict = PyDict::new(py);
                    total_dict.set_item("h1", total.h1())?;
                    total_dict.set_item("h2", total.h2())?;
                    total_dict.set_item("N1", total.n1())?;
                    total_dict.set_item("N2", total.n2())?;
                    total_dict.set_item("vocabulary", total.vocabulary())?;
                    total_dict.set_item("length", total.length())?;
                    total_dict.set_item("volume", total.volume())?;
                    total_dict.set_item("difficulty", total.difficulty())?;
                    total_dict.set_item("effort", total.effort())?;
                    total_dict.set_item("lineno", py.None())?;
                    total_dict.set_item("endline", py.None())?;
                    
                    hal_dict.set_item("detailed", detailed_dict)?;
                    hal_dict.set_item("total", total_dict)?;
                }
                Err(_) => {
                    let detailed_dict = PyDict::new(py);
                    let total_dict = PyDict::new(py);
                    total_dict.set_item("h1", 0)?;
                    total_dict.set_item("h2", 0)?;
                    total_dict.set_item("N1", 0)?;
                    total_dict.set_item("N2", 0)?;
                    total_dict.set_item("vocabulary", 0)?;
                    total_dict.set_item("length", 0)?;
                    total_dict.set_item("volume", 0.0)?;
                    total_dict.set_item("difficulty", 0.0)?;
                    total_dict.set_item("effort", 0.0)?;
                    total_dict.set_item("lineno", py.None())?;
                    total_dict.set_item("endline", py.None())?;
                    hal_dict.set_item("detailed", detailed_dict)?;
                    hal_dict.set_item("total", total_dict)?;
                }
            }
            file_dict.set_item("halstead", hal_dict)?;
        }

        // Maintainability Index
        if include_maintainability {
            let (mi, rank) = maintainability::analyze_source_mi(&source, multi);
            let mi_dict = PyDict::new(py);
            let total_dict = PyDict::new(py);
            total_dict.set_item("mi", mi)?;
            total_dict.set_item("rank", rank)?;
            mi_dict.set_item("total", total_dict)?;
            file_dict.set_item("maintainability", mi_dict)?;
        }

        output.set_item(&path, file_dict)?;
    }

    Ok(output)
}

/// Register the parallel module with the Python module.
pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(analyze_files_parallel, parent_module)?)?;
    Ok(())
}
