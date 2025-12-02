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
use pyo3::types::PyDict;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;

use crate::cyclomatic::{self, ClassComplexity, FunctionComplexity};
use crate::halstead::{self, FunctionHalstead, HalsteadMetrics};
use crate::maintainability;
use crate::raw;

// ============================================================================
// Thread-safe Rust structures matching Python dict output format exactly.
// Using #[derive(IntoPyObject)] with #[pyo3(item = "...")] for field renaming.
// ============================================================================

/// Raw metrics - wraps HashMap in {"total": {...}} structure
#[derive(Debug, Clone, IntoPyObject)]
struct RawResult {
    total: HashMap<String, i64>,
}

/// Cyclomatic function result - leaf struct with derive
#[derive(Debug, Clone, IntoPyObject)]
struct CyclomaticFunctionResult {
    name: String,
    is_method: bool,
    classname: Option<String>,
    complexity: u32,
    lineno: u32,
    endline: u32,
    loc: i64,
    closures: Vec<String>, // Always empty, but needed for Python compatibility
}

/// Cyclomatic class result - leaf struct with derive
#[derive(Debug, Clone, IntoPyObject)]
struct CyclomaticClassResult {
    name: String,
    complexity: u32,
    real_complexity: u32,
    lineno: u32,
    endline: u32,
    loc: i64,
    inner_classes: Vec<String>, // Always empty, but needed for Python compatibility
}

/// Cyclomatic total - just complexity
#[derive(Debug, Clone, IntoPyObject)]
struct CyclomaticTotal {
    complexity: i64,
}

/// Full cyclomatic result with detailed dict keyed by function/class name
#[derive(Debug, Clone)]
struct CyclomaticResult {
    functions: Vec<(String, CyclomaticFunctionResult)>, // (fullname, result)
    classes: Vec<(String, CyclomaticClassResult)>,      // (name, result)
    total_complexity: i64,
}

impl<'py> IntoPyObject<'py> for CyclomaticResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let detailed = PyDict::new(py);

        for (fullname, func) in self.functions {
            detailed.set_item(fullname, func.into_pyobject(py)?)?;
        }
        for (name, cls) in self.classes {
            detailed.set_item(name, cls.into_pyobject(py)?)?;
        }

        let total = CyclomaticTotal { complexity: self.total_complexity };
        dict.set_item("detailed", detailed)?;
        dict.set_item("total", total.into_pyobject(py)?)?;
        Ok(dict)
    }
}

/// Halstead function result - uses #[pyo3(item)] for N1/N2 naming
#[derive(Debug, Clone, IntoPyObject)]
struct HalsteadFunctionResult {
    h1: u32,
    h2: u32,
    #[pyo3(item("N1"))]
    n1: u32,
    #[pyo3(item("N2"))]
    n2: u32,
    vocabulary: u32,
    length: u32,
    volume: f64,
    difficulty: f64,
    effort: f64,
    lineno: u32,
    endline: u32,
}

/// Halstead total result - includes None for lineno/endline
#[derive(Debug, Clone, IntoPyObject)]
struct HalsteadTotalResult {
    h1: u32,
    h2: u32,
    #[pyo3(item("N1"))]
    n1: u32,
    #[pyo3(item("N2"))]
    n2: u32,
    vocabulary: u32,
    length: u32,
    volume: f64,
    difficulty: f64,
    effort: f64,
    lineno: Option<u32>,  // Always None
    endline: Option<u32>, // Always None
}

/// Full halstead result with detailed dict keyed by function name
#[derive(Debug, Clone)]
struct HalsteadResult {
    functions: Vec<(String, HalsteadFunctionResult)>, // (name, result)
    total: HalsteadTotalResult,
}

impl<'py> IntoPyObject<'py> for HalsteadResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let detailed = PyDict::new(py);

        for (name, func) in self.functions {
            detailed.set_item(name, func.into_pyobject(py)?)?;
        }

        dict.set_item("detailed", detailed)?;
        dict.set_item("total", self.total.into_pyobject(py)?)?;
        Ok(dict)
    }
}

/// Maintainability total
#[derive(Debug, Clone, IntoPyObject)]
struct MaintainabilityTotal {
    mi: f64,
    rank: String,
}

/// Maintainability result - wraps in {"total": {...}}
#[derive(Debug, Clone, IntoPyObject)]
struct MaintainabilityResult {
    total: MaintainabilityTotal,
}

/// Complete analysis result for a single file
#[derive(Debug, Clone)]
enum FileAnalysisResult {
    Success {
        raw: Option<RawResult>,
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

    let func_results: Vec<(String, CyclomaticFunctionResult)> = functions
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
            let lineno_val = (lineno.to_zero_indexed() + 1) as u32;
            let endline_val = (endline.to_zero_indexed() + 1) as u32;

            (
                func.fullname(),
                CyclomaticFunctionResult {
                    name: func.name.clone(),
                    is_method: func.is_method,
                    classname: func.classname.clone(),
                    complexity: func.complexity,
                    lineno: lineno_val,
                    endline: endline_val,
                    loc: endline_val as i64 - lineno_val as i64,
                    closures: Vec::new(),
                },
            )
        })
        .collect();

    let class_results: Vec<(String, CyclomaticClassResult)> = classes
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
            let lineno_val = (lineno.to_zero_indexed() + 1) as u32;
            let endline_val = (endline.to_zero_indexed() + 1) as u32;

            (
                cls.name.clone(),
                CyclomaticClassResult {
                    name: cls.name.clone(),
                    complexity: cls.complexity(),
                    real_complexity: cls.real_complexity,
                    lineno: lineno_val,
                    endline: endline_val,
                    loc: endline_val as i64 - lineno_val as i64,
                    inner_classes: Vec::new(),
                },
            )
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
    let func_results: Vec<(String, HalsteadFunctionResult)> = functions
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

            (
                func.name.clone(),
                HalsteadFunctionResult {
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
                },
            )
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
            lineno: None,
            endline: None,
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
        Some(RawResult {
            total: raw::analyze_source_raw(source),
        })
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
                    lineno: None,
                    endline: None,
                },
            }),
        }
    } else {
        None
    };

    let maintainability = if include_maintainability {
        let (mi, rank) = maintainability::analyze_source_mi(source, multi);
        Some(MaintainabilityResult {
            total: MaintainabilityTotal { mi, rank },
        })
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
    // This is a simple data transformation using IntoPyObject trait.
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
                if let Some(raw_result) = raw {
                    file_dict.set_item("raw", raw_result.into_pyobject(py)?)?;
                }
                if let Some(cc_result) = cyclomatic {
                    file_dict.set_item("cyclomatic", cc_result.into_pyobject(py)?)?;
                }
                if let Some(hal_result) = halstead {
                    file_dict.set_item("halstead", hal_result.into_pyobject(py)?)?;
                }
                if let Some(mi_result) = maintainability {
                    file_dict.set_item("maintainability", mi_result.into_pyobject(py)?)?;
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
