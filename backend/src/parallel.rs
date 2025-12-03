use pyo3::prelude::*;
use pyo3::types::PyDict;
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::fs;

use crate::cyclomatic::{self, ClassComplexity, FunctionComplexity};
use crate::halstead::{self, FunctionHalstead, HalsteadMetrics};
use crate::maintainability;
use crate::raw;

// ============================================================================
// Aggregation helpers
// ============================================================================

/// Get all parent directory paths from a file path (Unix-style).
/// e.g., "src/foo/bar.py" -> ["", "src", "src/foo"]
fn get_parent_paths(file_path: &str) -> Vec<String> {
    let mut paths = vec!["".to_string()]; // Root is always included
    
    if let Some(last_slash) = file_path.rfind('/') {
        let dir_part = &file_path[..last_slash];
        let mut current = String::new();
        
        for component in dir_part.split('/') {
            if !component.is_empty() {
                if current.is_empty() {
                    current = component.to_string();
                } else {
                    current = format!("{}/{}", current, component);
                }
                paths.push(current.clone());
            }
        }
    }
    
    paths
}

/// Collect all unique directory paths from a set of file paths
fn collect_all_directories(file_paths: &[String]) -> HashSet<String> {
    let mut dirs = HashSet::new();
    for path in file_paths {
        for dir in get_parent_paths(path) {
            dirs.insert(dir);
        }
    }
    dirs
}

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
    closures: Vec<String>, // Always empty, but needed for wily1 compatibility
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
    inner_classes: Vec<String>, // Always empty, but needed for wily1 compatibility
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
// Aggregation structs for directory-level metrics
// ============================================================================

/// Aggregated raw metrics for a directory
#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedRawResult {
    total: HashMap<String, i64>,
}

/// Aggregated cyclomatic metrics for a directory  
#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedCyclomaticResult {
    total: AggregatedCyclomaticTotal,
}

#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedCyclomaticTotal {
    complexity: f64,  // Mean of complexities
}

/// Aggregated halstead metrics for a directory
#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedHalsteadResult {
    total: AggregatedHalsteadTotal,
}

#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedHalsteadTotal {
    h1: i64,
    h2: i64,
    #[pyo3(item("N1"))]
    n1: i64,
    #[pyo3(item("N2"))]
    n2: i64,
    vocabulary: i64,
    length: i64,
    volume: f64,
    difficulty: f64,
    effort: f64,
}

/// Aggregated maintainability metrics for a directory
#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedMaintainabilityResult {
    total: AggregatedMaintainabilityTotal,
}

#[derive(Debug, Clone, IntoPyObject)]
struct AggregatedMaintainabilityTotal {
    mi: f64,   // Mean of MI values
    rank: String,  // Mode of ranks
}

/// Aggregate results for a directory
#[derive(Debug, Clone)]
struct DirectoryAggregate {
    raw: Option<AggregatedRawResult>,
    cyclomatic: Option<AggregatedCyclomaticResult>,
    halstead: Option<AggregatedHalsteadResult>,
    maintainability: Option<AggregatedMaintainabilityResult>,
}

/// Compute aggregate metrics for all directories from file results
fn compute_aggregates(
    file_results: &HashMap<String, FileAnalysisResult>,
    directories: &HashSet<String>,
) -> HashMap<String, DirectoryAggregate> {
    let mut aggregates = HashMap::new();
    
    for dir in directories {
        // Collect all file paths that belong to this directory
        let matching_files: Vec<&String> = file_results.keys()
            .filter(|path| {
                if dir.is_empty() {
                    true // Root matches all
                } else {
                    path.starts_with(dir) && 
                    (path.len() == dir.len() || path.chars().nth(dir.len()) == Some('/'))
                }
            })
            .collect();
        
        if matching_files.is_empty() {
            continue;
        }
        
        // Aggregate raw metrics (all use sum)
        let raw_agg = aggregate_raw_metrics(file_results, &matching_files);
        
        // Aggregate cyclomatic (uses mean)
        let cyclomatic_agg = aggregate_cyclomatic_metrics(file_results, &matching_files);
        
        // Aggregate halstead (all use sum)
        let halstead_agg = aggregate_halstead_metrics(file_results, &matching_files);
        
        // Aggregate maintainability (mi uses mean, rank uses mode)
        let maintainability_agg = aggregate_maintainability_metrics(file_results, &matching_files);
        
        aggregates.insert(dir.clone(), DirectoryAggregate {
            raw: raw_agg,
            cyclomatic: cyclomatic_agg,
            halstead: halstead_agg,
            maintainability: maintainability_agg,
        });
    }
    
    aggregates
}

fn aggregate_raw_metrics(
    file_results: &HashMap<String, FileAnalysisResult>,
    matching_files: &[&String],
) -> Option<AggregatedRawResult> {
    let mut totals: HashMap<String, i64> = HashMap::new();
    let mut has_data = false;
    
    for path in matching_files {
        if let Some(FileAnalysisResult::Success { raw: Some(raw), .. }) = file_results.get(*path) {
            has_data = true;
            for (key, value) in &raw.total {
                *totals.entry(key.clone()).or_insert(0) += value;
            }
        }
    }
    
    if has_data {
        Some(AggregatedRawResult { total: totals })
    } else {
        None
    }
}

fn aggregate_cyclomatic_metrics(
    file_results: &HashMap<String, FileAnalysisResult>,
    matching_files: &[&String],
) -> Option<AggregatedCyclomaticResult> {
    let mut complexities: Vec<i64> = Vec::new();
    
    for path in matching_files {
        if let Some(FileAnalysisResult::Success { cyclomatic: Some(cc), .. }) = file_results.get(*path) {
            complexities.push(cc.total_complexity);
        }
    }
    
    if complexities.is_empty() {
        None
    } else {
        let mean = complexities.iter().sum::<i64>() as f64 / complexities.len() as f64;
        Some(AggregatedCyclomaticResult {
            total: AggregatedCyclomaticTotal { complexity: mean },
        })
    }
}

fn aggregate_halstead_metrics(
    file_results: &HashMap<String, FileAnalysisResult>,
    matching_files: &[&String],
) -> Option<AggregatedHalsteadResult> {
    let mut h1_sum: i64 = 0;
    let mut h2_sum: i64 = 0;
    let mut n1_sum: i64 = 0;
    let mut n2_sum: i64 = 0;
    let mut vocab_sum: i64 = 0;
    let mut length_sum: i64 = 0;
    let mut volume_sum: f64 = 0.0;
    let mut difficulty_sum: f64 = 0.0;
    let mut effort_sum: f64 = 0.0;
    let mut has_data = false;
    
    for path in matching_files {
        if let Some(FileAnalysisResult::Success { halstead: Some(hal), .. }) = file_results.get(*path) {
            has_data = true;
            h1_sum += hal.total.h1 as i64;
            h2_sum += hal.total.h2 as i64;
            n1_sum += hal.total.n1 as i64;
            n2_sum += hal.total.n2 as i64;
            vocab_sum += hal.total.vocabulary as i64;
            length_sum += hal.total.length as i64;
            volume_sum += hal.total.volume;
            difficulty_sum += hal.total.difficulty;
            effort_sum += hal.total.effort;
        }
    }
    
    if has_data {
        Some(AggregatedHalsteadResult {
            total: AggregatedHalsteadTotal {
                h1: h1_sum,
                h2: h2_sum,
                n1: n1_sum,
                n2: n2_sum,
                vocabulary: vocab_sum,
                length: length_sum,
                volume: volume_sum,
                difficulty: difficulty_sum,
                effort: effort_sum,
            },
        })
    } else {
        None
    }
}

fn aggregate_maintainability_metrics(
    file_results: &HashMap<String, FileAnalysisResult>,
    matching_files: &[&String],
) -> Option<AggregatedMaintainabilityResult> {
    let mut mi_values: Vec<f64> = Vec::new();
    let mut rank_counts: HashMap<String, usize> = HashMap::new();
    
    for path in matching_files {
        if let Some(FileAnalysisResult::Success { maintainability: Some(mi), .. }) = file_results.get(*path) {
            mi_values.push(mi.total.mi);
            *rank_counts.entry(mi.total.rank.clone()).or_insert(0) += 1;
        }
    }
    
    if mi_values.is_empty() {
        None
    } else {
        let mean_mi = mi_values.iter().sum::<f64>() / mi_values.len() as f64;
        // Mode of ranks
        let mode_rank = rank_counts
            .into_iter()
            .max_by_key(|(_, count)| *count)
            .map(|(rank, _)| rank)
            .unwrap_or_else(|| "A".to_string());
        
        Some(AggregatedMaintainabilityResult {
            total: AggregatedMaintainabilityTotal {
                mi: mean_mi,
                rank: mode_rank,
            },
        })
    }
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
/// 3. Aggregation computation
///
/// Python dict creation happens after all parallel work is complete.
///
/// # Arguments
/// * `paths` - List of file paths to analyze
/// * `operators` - List of operator names to run ("raw", "cyclomatic", "halstead", "maintainability")
/// * `multi` - Whether to include multi-line strings in MI calculation
///
/// # Returns
/// A dictionary mapping file paths (and directory paths) to their analysis results.
/// Directory paths contain aggregated metrics from all files within them.
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

    // Phase 1: Parallel file analysis (GIL released)
    let (analysis_results, directories): (HashMap<String, FileAnalysisResult>, HashSet<String>) = 
        py.detach(|| {
            // Collect all directory paths first
            let dirs = collect_all_directories(&paths);
            
            // Analyze files in parallel
            let results: HashMap<String, FileAnalysisResult> = paths
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
                .collect();
            
            (results, dirs)
        });

    // Phase 2: Compute aggregates (still outside GIL if possible)
    let aggregates = compute_aggregates(&analysis_results, &directories);

    // Phase 3: Convert to Python dicts (requires GIL)
    let output = PyDict::new(py);

    // Add file results
    for (path, result) in &analysis_results {
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
                    file_dict.set_item("raw", raw_result.clone().into_pyobject(py)?)?;
                }
                if let Some(cc_result) = cyclomatic {
                    file_dict.set_item("cyclomatic", cc_result.clone().into_pyobject(py)?)?;
                }
                if let Some(hal_result) = halstead {
                    file_dict.set_item("halstead", hal_result.clone().into_pyobject(py)?)?;
                }
                if let Some(mi_result) = maintainability {
                    file_dict.set_item("maintainability", mi_result.clone().into_pyobject(py)?)?;
                }
            }
        }

        output.set_item(path, file_dict)?;
    }

    // Add directory aggregates
    for (dir_path, aggregate) in aggregates {
        let dir_dict = PyDict::new(py);

        if let Some(raw_agg) = aggregate.raw {
            dir_dict.set_item("raw", raw_agg.into_pyobject(py)?)?;
        }
        if let Some(cc_agg) = aggregate.cyclomatic {
            dir_dict.set_item("cyclomatic", cc_agg.into_pyobject(py)?)?;
        }
        if let Some(hal_agg) = aggregate.halstead {
            dir_dict.set_item("halstead", hal_agg.into_pyobject(py)?)?;
        }
        if let Some(mi_agg) = aggregate.maintainability {
            dir_dict.set_item("maintainability", mi_agg.into_pyobject(py)?)?;
        }

        output.set_item(&dir_path, dir_dict)?;
    }

    Ok(output)
}

pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(analyze_files_parallel, parent_module)?)?;
    Ok(())
}
