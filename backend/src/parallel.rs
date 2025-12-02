//! Parallel file analysis using rayon.
//!
//! This module provides efficient parallel processing of Python files,
//! replacing Python's multiprocessing.Pool with Rust's rayon thread pool.
//!
//! The key design principle is to maximize work done outside the GIL:
//! 1. Read all files in parallel (no GIL needed)
//! 2. Analyze all files in parallel (no GIL needed)  
//! 3. Store results in thread-safe Rust structures
//! 4. Convert to Python dicts only after parallel work is complete

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;

use crate::cyclomatic::{self, ClassComplexity, FunctionComplexity};
use crate::halstead::{self, FunctionHalstead, HalsteadMetrics};
use crate::maintainability;
use crate::raw;

// ============================================================================
// Thread-safe Rust structures to hold analysis results
// ============================================================================

/// Raw metrics result (already a HashMap from raw module)
type RawMetricsResult = HashMap<String, i64>;

/// Cyclomatic complexity results stored without LineIndex
#[derive(Debug, Clone)]
struct CyclomaticFunctionResult {
    name: String,
    fullname: String,
    is_method: bool,
    classname: Option<String>,
    complexity: u32,
    lineno: u32,
    endline: u32,
}

#[derive(Debug, Clone)]
struct CyclomaticClassResult {
    name: String,
    complexity: u32,
    real_complexity: u32,
    lineno: u32,
    endline: u32,
}

#[derive(Debug, Clone)]
struct CyclomaticResult {
    functions: Vec<CyclomaticFunctionResult>,
    classes: Vec<CyclomaticClassResult>,
    total_complexity: i64,
}

/// Halstead metrics results stored without LineIndex
#[derive(Debug, Clone)]
struct HalsteadFunctionResult {
    name: String,
    h1: u32,
    h2: u32,
    n1: u32,
    n2: u32,
    vocabulary: u32,
    length: u32,
    volume: f64,
    difficulty: f64,
    effort: f64,
    lineno: u32,
    endline: u32,
}

#[derive(Debug, Clone)]
struct HalsteadTotalResult {
    h1: u32,
    h2: u32,
    n1: u32,
    n2: u32,
    vocabulary: u32,
    length: u32,
    volume: f64,
    difficulty: f64,
    effort: f64,
}

#[derive(Debug, Clone)]
struct HalsteadResult {
    functions: Vec<HalsteadFunctionResult>,
    total: HalsteadTotalResult,
}

/// Maintainability index result
#[derive(Debug, Clone)]
struct MaintainabilityResult {
    mi: f64,
    rank: String,
}

/// Complete analysis result for a single file
#[derive(Debug, Clone)]
enum FileAnalysisResult {
    Success {
        raw: Option<RawMetricsResult>,
        cyclomatic: Option<CyclomaticResult>,
        halstead: Option<HalsteadResult>,
        maintainability: Option<MaintainabilityResult>,
    },
    Error(String),
}

// ============================================================================
// Conversion functions from internal types to our thread-safe structs
// ============================================================================

fn convert_cyclomatic(
    functions: Vec<FunctionComplexity>,
    classes: Vec<ClassComplexity>,
    line_index: &ruff_source_file::LineIndex,
) -> CyclomaticResult {
    let mut total_complexity: i64 = 0;

    let func_results: Vec<CyclomaticFunctionResult> = functions
        .iter()
        .map(|func| {
            let lineno = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(func.start_offset),
            );
            let endline = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(func.end_offset),
            );
            total_complexity += func.complexity as i64;

            CyclomaticFunctionResult {
                name: func.name.clone(),
                fullname: func.fullname(),
                is_method: func.is_method,
                classname: func.classname.clone(),
                complexity: func.complexity,
                lineno: (lineno.to_zero_indexed() + 1) as u32,
                endline: (endline.to_zero_indexed() + 1) as u32,
            }
        })
        .collect();

    let class_results: Vec<CyclomaticClassResult> = classes
        .iter()
        .map(|cls| {
            let lineno = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(cls.start_offset),
            );
            let endline = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(cls.end_offset),
            );
            total_complexity += cls.complexity() as i64;

            CyclomaticClassResult {
                name: cls.name.clone(),
                complexity: cls.complexity(),
                real_complexity: cls.real_complexity,
                lineno: (lineno.to_zero_indexed() + 1) as u32,
                endline: (endline.to_zero_indexed() + 1) as u32,
            }
        })
        .collect();

    CyclomaticResult {
        functions: func_results,
        classes: class_results,
        total_complexity,
    }
}

fn convert_halstead(
    functions: Vec<FunctionHalstead>,
    total: HalsteadMetrics,
    line_index: &ruff_source_file::LineIndex,
) -> HalsteadResult {
    let func_results: Vec<HalsteadFunctionResult> = functions
        .iter()
        .map(|func| {
            let lineno = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(func.start_offset),
            );
            let endline = ruff_source_file::LineIndex::line_index(
                line_index,
                ruff_text_size::TextSize::new(func.end_offset),
            );

            HalsteadFunctionResult {
                name: func.name.clone(),
                h1: func.metrics.h1(),
                h2: func.metrics.h2(),
                n1: func.metrics.n1(),
                n2: func.metrics.n2(),
                vocabulary: func.metrics.vocabulary(),
                length: func.metrics.length(),
                volume: func.metrics.volume(),
                difficulty: func.metrics.difficulty(),
                effort: func.metrics.effort(),
                lineno: (lineno.to_zero_indexed() + 1) as u32,
                endline: (endline.to_zero_indexed() + 1) as u32,
            }
        })
        .collect();

    HalsteadResult {
        functions: func_results,
        total: HalsteadTotalResult {
            h1: total.h1(),
            h2: total.h2(),
            n1: total.n1(),
            n2: total.n2(),
            vocabulary: total.vocabulary(),
            length: total.length(),
            volume: total.volume(),
            difficulty: total.difficulty(),
            effort: total.effort(),
        },
    }
}

/// Analyze a single file and return thread-safe results
fn analyze_file(
    source: &str,
    include_raw: bool,
    include_cyclomatic: bool,
    include_halstead: bool,
    include_maintainability: bool,
    multi: bool,
) -> FileAnalysisResult {
    let raw = if include_raw {
        Some(raw::analyze_source_raw(source))
    } else {
        None
    };

    let cyclomatic = if include_cyclomatic {
        match cyclomatic::analyze_source_full(source) {
            Ok((functions, classes, line_index)) => {
                Some(convert_cyclomatic(functions, classes, &line_index))
            }
            Err(_) => Some(CyclomaticResult {
                functions: Vec::new(),
                classes: Vec::new(),
                total_complexity: 0,
            }),
        }
    } else {
        None
    };

    let halstead = if include_halstead {
        match halstead::analyze_source_full(source) {
            Ok((functions, total, line_index)) => {
                Some(convert_halstead(functions, total, &line_index))
            }
            Err(_) => Some(HalsteadResult {
                functions: Vec::new(),
                total: HalsteadTotalResult {
                    h1: 0,
                    h2: 0,
                    n1: 0,
                    n2: 0,
                    vocabulary: 0,
                    length: 0,
                    volume: 0.0,
                    difficulty: 0.0,
                    effort: 0.0,
                },
            }),
        }
    } else {
        None
    };

    let maintainability = if include_maintainability {
        let (mi, rank) = maintainability::analyze_source_mi(source, multi);
        Some(MaintainabilityResult { mi, rank })
    } else {
        None
    };

    FileAnalysisResult::Success {
        raw,
        cyclomatic,
        halstead,
        maintainability,
    }
}

// ============================================================================
// Python conversion functions
// ============================================================================

fn cyclomatic_to_pydict<'py>(
    py: Python<'py>,
    result: &CyclomaticResult,
) -> PyResult<Bound<'py, PyDict>> {
    let cc_dict = PyDict::new(py);
    let detailed_dict = PyDict::new(py);

    for func in &result.functions {
        let func_dict = PyDict::new(py);
        func_dict.set_item("name", &func.name)?;
        func_dict.set_item("is_method", func.is_method)?;
        func_dict.set_item("classname", func.classname.as_deref())?;
        func_dict.set_item("complexity", func.complexity)?;
        func_dict.set_item("lineno", func.lineno)?;
        func_dict.set_item("endline", func.endline)?;
        func_dict.set_item("loc", func.endline as i64 - func.lineno as i64)?;

        let closures_list = PyList::empty(py);
        func_dict.set_item("closures", closures_list)?;

        detailed_dict.set_item(func.fullname.as_str(), func_dict)?;
    }

    for cls in &result.classes {
        let cls_dict = PyDict::new(py);
        cls_dict.set_item("name", &cls.name)?;
        cls_dict.set_item("complexity", cls.complexity)?;
        cls_dict.set_item("real_complexity", cls.real_complexity)?;
        cls_dict.set_item("lineno", cls.lineno)?;
        cls_dict.set_item("endline", cls.endline)?;
        cls_dict.set_item("loc", cls.endline as i64 - cls.lineno as i64)?;

        let inner_classes_list = PyList::empty(py);
        cls_dict.set_item("inner_classes", inner_classes_list)?;

        detailed_dict.set_item(cls.name.as_str(), cls_dict)?;
    }

    let total_dict = PyDict::new(py);
    total_dict.set_item("complexity", result.total_complexity)?;
    cc_dict.set_item("detailed", detailed_dict)?;
    cc_dict.set_item("total", total_dict)?;

    Ok(cc_dict)
}

fn halstead_to_pydict<'py>(
    py: Python<'py>,
    result: &HalsteadResult,
) -> PyResult<Bound<'py, PyDict>> {
    let hal_dict = PyDict::new(py);
    let detailed_dict = PyDict::new(py);

    for func in &result.functions {
        let func_dict = PyDict::new(py);
        func_dict.set_item("h1", func.h1)?;
        func_dict.set_item("h2", func.h2)?;
        func_dict.set_item("N1", func.n1)?;
        func_dict.set_item("N2", func.n2)?;
        func_dict.set_item("vocabulary", func.vocabulary)?;
        func_dict.set_item("length", func.length)?;
        func_dict.set_item("volume", func.volume)?;
        func_dict.set_item("difficulty", func.difficulty)?;
        func_dict.set_item("effort", func.effort)?;
        func_dict.set_item("lineno", func.lineno)?;
        func_dict.set_item("endline", func.endline)?;

        detailed_dict.set_item(func.name.as_str(), func_dict)?;
    }

    let total_dict = PyDict::new(py);
    total_dict.set_item("h1", result.total.h1)?;
    total_dict.set_item("h2", result.total.h2)?;
    total_dict.set_item("N1", result.total.n1)?;
    total_dict.set_item("N2", result.total.n2)?;
    total_dict.set_item("vocabulary", result.total.vocabulary)?;
    total_dict.set_item("length", result.total.length)?;
    total_dict.set_item("volume", result.total.volume)?;
    total_dict.set_item("difficulty", result.total.difficulty)?;
    total_dict.set_item("effort", result.total.effort)?;
    total_dict.set_item("lineno", py.None())?;
    total_dict.set_item("endline", py.None())?;

    hal_dict.set_item("detailed", detailed_dict)?;
    hal_dict.set_item("total", total_dict)?;

    Ok(hal_dict)
}

fn raw_to_pydict<'py>(py: Python<'py>, metrics: &RawMetricsResult) -> PyResult<Bound<'py, PyDict>> {
    let raw_dict = PyDict::new(py);
    let total_dict = PyDict::new(py);
    for (key, value) in metrics {
        total_dict.set_item(key.as_str(), *value)?;
    }
    raw_dict.set_item("total", total_dict)?;
    Ok(raw_dict)
}

fn maintainability_to_pydict<'py>(
    py: Python<'py>,
    result: &MaintainabilityResult,
) -> PyResult<Bound<'py, PyDict>> {
    let mi_dict = PyDict::new(py);
    let total_dict = PyDict::new(py);
    total_dict.set_item("mi", result.mi)?;
    total_dict.set_item("rank", result.rank.as_str())?;
    mi_dict.set_item("total", total_dict)?;
    Ok(mi_dict)
}

// ============================================================================
// Main public function
// ============================================================================

/// Analyze multiple files in parallel using rayon.
///
/// This function replaces Python's multiprocessing.Pool with Rust's rayon
/// thread pool, which is more efficient for CPU-bound tasks.
///
/// The GIL is released during:
/// 1. File reading (parallel I/O)
/// 2. Metric computation (parallel CPU work)
///
/// Python dict creation happens after all parallel work is complete.
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

    // ========================================================================
    // PHASE 1: Parallel file reading and analysis (GIL released)
    // ========================================================================
    // All heavy computation happens here, outside the GIL.
    // Results are stored in thread-safe Rust structures.
    let analysis_results: Vec<(String, FileAnalysisResult)> = py.detach(|| {
        paths
            .par_iter()
            .map(|path| {
                // Read file
                let content = match fs::read_to_string(path) {
                    Ok(s) => s,
                    Err(e) => {
                        return (
                            path.clone(),
                            FileAnalysisResult::Error(format!("Failed to read file: {}", e)),
                        );
                    }
                };

                // Analyze file (all operators at once)
                let result = analyze_file(
                    &content,
                    include_raw,
                    include_cyclomatic,
                    include_halstead,
                    include_maintainability,
                    multi,
                );

                (path.clone(), result)
            })
            .collect()
    });

    // ========================================================================
    // PHASE 2: Convert Rust results to Python dicts (GIL held)
    // ========================================================================
    // This is a simple data transformation, no heavy computation.
    let output = PyDict::new(py);

    for (path, result) in analysis_results {
        let file_dict = PyDict::new(py);

        match result {
            FileAnalysisResult::Error(e) => {
                file_dict.set_item("error", e)?;
            }
            FileAnalysisResult::Success {
                raw,
                cyclomatic,
                halstead,
                maintainability,
            } => {
                if let Some(ref raw_metrics) = raw {
                    file_dict.set_item("raw", raw_to_pydict(py, raw_metrics)?)?;
                }
                if let Some(ref cc_result) = cyclomatic {
                    file_dict.set_item("cyclomatic", cyclomatic_to_pydict(py, cc_result)?)?;
                }
                if let Some(ref hal_result) = halstead {
                    file_dict.set_item("halstead", halstead_to_pydict(py, hal_result)?)?;
                }
                if let Some(ref mi_result) = maintainability {
                    file_dict
                        .set_item("maintainability", maintainability_to_pydict(py, mi_result)?)?;
                }
            }
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
