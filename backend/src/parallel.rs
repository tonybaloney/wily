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
// These implement IntoPyObject for automatic Python dict conversion
// ============================================================================

/// Raw metrics result (already a HashMap from raw module)
type RawMetricsResult = HashMap<String, i64>;

/// Wrapper for raw metrics that converts to Python dict with "total" key
#[derive(Debug, Clone)]
struct RawResult {
    metrics: RawMetricsResult,
}

impl<'py> IntoPyObject<'py> for RawResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let total = PyDict::new(py);
        for (key, value) in self.metrics {
            total.set_item(key, value)?;
        }
        dict.set_item("total", total)?;
        Ok(dict)
    }
}

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

impl<'py> IntoPyObject<'py> for CyclomaticFunctionResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        dict.set_item("name", self.name)?;
        dict.set_item("is_method", self.is_method)?;
        dict.set_item("classname", self.classname)?;
        dict.set_item("complexity", self.complexity)?;
        dict.set_item("lineno", self.lineno)?;
        dict.set_item("endline", self.endline)?;
        dict.set_item("loc", self.endline as i64 - self.lineno as i64)?;
        dict.set_item("closures", PyList::empty(py))?;
        Ok(dict)
    }
}

#[derive(Debug, Clone)]
struct CyclomaticClassResult {
    name: String,
    complexity: u32,
    real_complexity: u32,
    lineno: u32,
    endline: u32,
}

impl<'py> IntoPyObject<'py> for CyclomaticClassResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        dict.set_item("name", &self.name)?;
        dict.set_item("complexity", self.complexity)?;
        dict.set_item("real_complexity", self.real_complexity)?;
        dict.set_item("lineno", self.lineno)?;
        dict.set_item("endline", self.endline)?;
        dict.set_item("loc", self.endline as i64 - self.lineno as i64)?;
        dict.set_item("inner_classes", PyList::empty(py))?;
        Ok(dict)
    }
}

#[derive(Debug, Clone)]
struct CyclomaticResult {
    functions: Vec<CyclomaticFunctionResult>,
    classes: Vec<CyclomaticClassResult>,
    total_complexity: i64,
}

impl<'py> IntoPyObject<'py> for CyclomaticResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let detailed = PyDict::new(py);

        for func in self.functions {
            let fullname = func.fullname.clone();
            detailed.set_item(fullname, func.into_pyobject(py)?)?;
        }
        for cls in self.classes {
            let name = cls.name.clone();
            detailed.set_item(name, cls.into_pyobject(py)?)?;
        }

        let total = PyDict::new(py);
        total.set_item("complexity", self.total_complexity)?;

        dict.set_item("detailed", detailed)?;
        dict.set_item("total", total)?;
        Ok(dict)
    }
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

impl<'py> IntoPyObject<'py> for HalsteadFunctionResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        dict.set_item("h1", self.h1)?;
        dict.set_item("h2", self.h2)?;
        dict.set_item("N1", self.n1)?;
        dict.set_item("N2", self.n2)?;
        dict.set_item("vocabulary", self.vocabulary)?;
        dict.set_item("length", self.length)?;
        dict.set_item("volume", self.volume)?;
        dict.set_item("difficulty", self.difficulty)?;
        dict.set_item("effort", self.effort)?;
        dict.set_item("lineno", self.lineno)?;
        dict.set_item("endline", self.endline)?;
        Ok(dict)
    }
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

impl<'py> IntoPyObject<'py> for HalsteadTotalResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        dict.set_item("h1", self.h1)?;
        dict.set_item("h2", self.h2)?;
        dict.set_item("N1", self.n1)?;
        dict.set_item("N2", self.n2)?;
        dict.set_item("vocabulary", self.vocabulary)?;
        dict.set_item("length", self.length)?;
        dict.set_item("volume", self.volume)?;
        dict.set_item("difficulty", self.difficulty)?;
        dict.set_item("effort", self.effort)?;
        dict.set_item("lineno", py.None())?;
        dict.set_item("endline", py.None())?;
        Ok(dict)
    }
}

#[derive(Debug, Clone)]
struct HalsteadResult {
    functions: Vec<HalsteadFunctionResult>,
    total: HalsteadTotalResult,
}

impl<'py> IntoPyObject<'py> for HalsteadResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let detailed = PyDict::new(py);

        for func in self.functions {
            let name = func.name.clone();
            detailed.set_item(name, func.into_pyobject(py)?)?;
        }

        dict.set_item("detailed", detailed)?;
        dict.set_item("total", self.total.into_pyobject(py)?)?;
        Ok(dict)
    }
}

/// Maintainability index result
#[derive(Debug, Clone)]
struct MaintainabilityResult {
    mi: f64,
    rank: String,
}

impl<'py> IntoPyObject<'py> for MaintainabilityResult {
    type Target = PyDict;
    type Output = Bound<'py, PyDict>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        let dict = PyDict::new(py);
        let total = PyDict::new(py);
        total.set_item("mi", self.mi)?;
        total.set_item("rank", self.rank)?;
        dict.set_item("total", total)?;
        Ok(dict)
    }
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
        Some(RawResult {
            metrics: raw::analyze_source_raw(source),
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
