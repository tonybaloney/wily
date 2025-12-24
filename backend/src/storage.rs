//! Parquet-based storage for wily metrics.
//!
//! This module provides high-performance columnar storage for code metrics.
//! All revisions are stored in a single parquet file per project.

use arrow::array::{
    ArrayRef, Float64Builder, Int64Builder, RecordBatch, StringBuilder, UInt32Builder,
};
use arrow::datatypes::{DataType, Field, Schema};
use parquet::arrow::ArrowWriter;
use parquet::basic::Compression;
use parquet::file::properties::WriterProperties;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::fs::File;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

// Type aliases for complex Halstead metric tuples to satisfy clippy
type HalsteadTotals = (u32, u32, u32, u32, u32, u32, f64, f64, f64);
type HalsteadFunctionMetrics = (
    String,
    u32,
    u32,
    u32,
    u32,
    u32,
    u32,
    f64,
    f64,
    f64,
    u32,
    u32,
);

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

/// Schema for the metrics table.
/// Each row represents metrics for a single path (file, directory, function, or class) in a single revision.
fn metrics_schema() -> Schema {
    Schema::new(vec![
        // Revision metadata
        Field::new("revision", DataType::Utf8, false),
        Field::new("revision_date", DataType::Int64, false), // Unix timestamp
        Field::new("revision_author", DataType::Utf8, true),
        Field::new("revision_message", DataType::Utf8, true),
        // Path identification
        Field::new("path", DataType::Utf8, false), // "" for root, "src/foo.py" for file, "src/foo.py:ClassName" for class
        Field::new("path_type", DataType::Utf8, false), // "root", "directory", "file", "function", "class"
        // Raw metrics
        Field::new("loc", DataType::Int64, true),
        Field::new("sloc", DataType::Int64, true),
        Field::new("lloc", DataType::Int64, true),
        Field::new("comments", DataType::Int64, true),
        Field::new("multi", DataType::Int64, true),
        Field::new("blank", DataType::Int64, true),
        Field::new("single_comments", DataType::Int64, true),
        // Cyclomatic complexity
        Field::new("complexity", DataType::Float64, true), // Float for aggregated values
        Field::new("real_complexity", DataType::UInt32, true), // For classes
        // Halstead metrics
        Field::new("h1", DataType::Int64, true),
        Field::new("h2", DataType::Int64, true),
        Field::new("N1", DataType::Int64, true),
        Field::new("N2", DataType::Int64, true),
        Field::new("vocabulary", DataType::Int64, true),
        Field::new("length", DataType::Int64, true),
        Field::new("volume", DataType::Float64, true),
        Field::new("difficulty", DataType::Float64, true),
        Field::new("effort", DataType::Float64, true),
        // Maintainability
        Field::new("mi", DataType::Float64, true),
        Field::new("rank", DataType::Utf8, true),
        // Function/class specific
        Field::new("lineno", DataType::UInt32, true),
        Field::new("endline", DataType::UInt32, true),
        Field::new("is_method", DataType::Boolean, true),
        Field::new("classname", DataType::Utf8, true),
    ])
}

/// A single row of metrics data, stored for querying.
#[derive(Clone, Debug)]
pub struct MetricRow {
    pub revision: String,
    pub revision_date: i64,
    pub revision_author: Option<String>,
    pub revision_message: Option<String>,
    pub path: String,
    pub path_type: String,
    pub loc: Option<i64>,
    pub sloc: Option<i64>,
    pub lloc: Option<i64>,
    pub comments: Option<i64>,
    pub multi: Option<i64>,
    pub blank: Option<i64>,
    pub single_comments: Option<i64>,
    pub complexity: Option<f64>,
    pub real_complexity: Option<u32>,
    pub h1: Option<i64>,
    pub h2: Option<i64>,
    pub n1: Option<i64>,
    pub n2: Option<i64>,
    pub vocabulary: Option<i64>,
    pub length: Option<i64>,
    pub volume: Option<f64>,
    pub difficulty: Option<f64>,
    pub effort: Option<f64>,
    pub mi: Option<f64>,
    pub rank: Option<String>,
    pub lineno: Option<u32>,
    pub endline: Option<u32>,
    pub is_method: Option<bool>,
    pub classname: Option<String>,
}

impl MetricRow {
    /// Convert this row to a Python dictionary.
    fn to_py_dict(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("revision", &self.revision)?;
        dict.set_item("revision_date", self.revision_date)?;
        dict.set_item("revision_author", &self.revision_author)?;
        dict.set_item("revision_message", &self.revision_message)?;
        dict.set_item("path", &self.path)?;
        dict.set_item("path_type", &self.path_type)?;
        dict.set_item("loc", self.loc)?;
        dict.set_item("sloc", self.sloc)?;
        dict.set_item("lloc", self.lloc)?;
        dict.set_item("comments", self.comments)?;
        dict.set_item("multi", self.multi)?;
        dict.set_item("blank", self.blank)?;
        dict.set_item("single_comments", self.single_comments)?;
        dict.set_item("complexity", self.complexity)?;
        dict.set_item("real_complexity", self.real_complexity)?;
        dict.set_item("h1", self.h1)?;
        dict.set_item("h2", self.h2)?;
        dict.set_item("N1", self.n1)?;
        dict.set_item("N2", self.n2)?;
        dict.set_item("vocabulary", self.vocabulary)?;
        dict.set_item("length", self.length)?;
        dict.set_item("volume", self.volume)?;
        dict.set_item("difficulty", self.difficulty)?;
        dict.set_item("effort", self.effort)?;
        dict.set_item("mi", self.mi)?;
        dict.set_item("rank", &self.rank)?;
        dict.set_item("lineno", self.lineno)?;
        dict.set_item("endline", self.endline)?;
        dict.set_item("is_method", self.is_method)?;
        dict.set_item("classname", &self.classname)?;
        Ok(dict.into())
    }
}

/// Builder for accumulating metric rows before writing to parquet.
pub struct MetricsBuilder {
    revision: StringBuilder,
    revision_date: Int64Builder,
    revision_author: StringBuilder,
    revision_message: StringBuilder,
    path: StringBuilder,
    path_type: StringBuilder,
    // Raw
    loc: Int64Builder,
    sloc: Int64Builder,
    lloc: Int64Builder,
    comments: Int64Builder,
    multi: Int64Builder,
    blank: Int64Builder,
    single_comments: Int64Builder,
    // Cyclomatic
    complexity: Float64Builder,
    real_complexity: UInt32Builder,
    // Halstead
    h1: Int64Builder,
    h2: Int64Builder,
    n1: Int64Builder,
    n2: Int64Builder,
    vocabulary: Int64Builder,
    length: Int64Builder,
    volume: Float64Builder,
    difficulty: Float64Builder,
    effort: Float64Builder,
    // Maintainability
    mi: Float64Builder,
    rank: StringBuilder,
    // Function/class
    lineno: UInt32Builder,
    endline: UInt32Builder,
    is_method: arrow::array::BooleanBuilder,
    classname: StringBuilder,
    // Row counter for is_empty check
    row_count: usize,
}

impl MetricsBuilder {
    pub fn new() -> Self {
        Self {
            revision: StringBuilder::new(),
            revision_date: Int64Builder::new(),
            revision_author: StringBuilder::new(),
            revision_message: StringBuilder::new(),
            path: StringBuilder::new(),
            path_type: StringBuilder::new(),
            loc: Int64Builder::new(),
            sloc: Int64Builder::new(),
            lloc: Int64Builder::new(),
            comments: Int64Builder::new(),
            multi: Int64Builder::new(),
            blank: Int64Builder::new(),
            single_comments: Int64Builder::new(),
            complexity: Float64Builder::new(),
            real_complexity: UInt32Builder::new(),
            h1: Int64Builder::new(),
            h2: Int64Builder::new(),
            n1: Int64Builder::new(),
            n2: Int64Builder::new(),
            vocabulary: Int64Builder::new(),
            length: Int64Builder::new(),
            volume: Float64Builder::new(),
            difficulty: Float64Builder::new(),
            effort: Float64Builder::new(),
            mi: Float64Builder::new(),
            rank: StringBuilder::new(),
            lineno: UInt32Builder::new(),
            endline: UInt32Builder::new(),
            is_method: arrow::array::BooleanBuilder::new(),
            classname: StringBuilder::new(),
            row_count: 0,
        }
    }

    /// Add a row with file-level or directory-level aggregate metrics.
    #[allow(clippy::too_many_arguments)]
    pub fn add_aggregate_row(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str,
        path_type: &str,
        // Raw metrics
        loc: Option<i64>,
        sloc: Option<i64>,
        lloc: Option<i64>,
        comments: Option<i64>,
        multi: Option<i64>,
        blank: Option<i64>,
        single_comments: Option<i64>,
        // Cyclomatic
        complexity: Option<f64>,
        // Halstead
        h1: Option<i64>,
        h2: Option<i64>,
        n1: Option<i64>,
        n2: Option<i64>,
        vocabulary: Option<i64>,
        length: Option<i64>,
        volume: Option<f64>,
        difficulty: Option<f64>,
        effort: Option<f64>,
        // Maintainability
        mi: Option<f64>,
        rank: Option<&str>,
    ) {
        self.revision.append_value(revision);
        self.revision_date.append_value(revision_date);
        self.revision_author.append_option(revision_author);
        self.revision_message.append_option(revision_message);
        self.path.append_value(path);
        self.path_type.append_value(path_type);

        self.loc.append_option(loc);
        self.sloc.append_option(sloc);
        self.lloc.append_option(lloc);
        self.comments.append_option(comments);
        self.multi.append_option(multi);
        self.blank.append_option(blank);
        self.single_comments.append_option(single_comments);

        self.complexity.append_option(complexity);
        self.real_complexity.append_null(); // Not for aggregates

        self.h1.append_option(h1);
        self.h2.append_option(h2);
        self.n1.append_option(n1);
        self.n2.append_option(n2);
        self.vocabulary.append_option(vocabulary);
        self.length.append_option(length);
        self.volume.append_option(volume);
        self.difficulty.append_option(difficulty);
        self.effort.append_option(effort);

        self.mi.append_option(mi);
        self.rank.append_option(rank);

        self.lineno.append_null();
        self.endline.append_null();
        self.is_method.append_null();
        self.classname.append_null();

        self.row_count += 1;
    }

    /// Add a row for a function.
    #[allow(clippy::too_many_arguments)]
    pub fn add_function_row(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str, // e.g., "src/foo.py:function_name" or "src/foo.py:ClassName.method_name"
        complexity: u32,
        lineno: u32,
        endline: u32,
        is_method: bool,
        classname: Option<&str>,
        // Halstead for function
        h1: Option<u32>,
        h2: Option<u32>,
        n1: Option<u32>,
        n2: Option<u32>,
        vocabulary: Option<u32>,
        length: Option<u32>,
        volume: Option<f64>,
        difficulty: Option<f64>,
        effort: Option<f64>,
    ) {
        self.revision.append_value(revision);
        self.revision_date.append_value(revision_date);
        self.revision_author.append_option(revision_author);
        self.revision_message.append_option(revision_message);
        self.path.append_value(path);
        self.path_type.append_value("function");

        // No raw metrics for functions
        self.loc.append_null();
        self.sloc.append_null();
        self.lloc.append_null();
        self.comments.append_null();
        self.multi.append_null();
        self.blank.append_null();
        self.single_comments.append_null();

        self.complexity.append_value(complexity as f64);
        self.real_complexity.append_null();

        self.h1.append_option(h1.map(|v| v as i64));
        self.h2.append_option(h2.map(|v| v as i64));
        self.n1.append_option(n1.map(|v| v as i64));
        self.n2.append_option(n2.map(|v| v as i64));
        self.vocabulary.append_option(vocabulary.map(|v| v as i64));
        self.length.append_option(length.map(|v| v as i64));
        self.volume.append_option(volume);
        self.difficulty.append_option(difficulty);
        self.effort.append_option(effort);

        self.mi.append_null();
        self.rank.append_null();

        self.lineno.append_value(lineno);
        self.endline.append_value(endline);
        self.is_method.append_value(is_method);
        self.classname.append_option(classname);

        self.row_count += 1;
    }

    /// Add a row for a class.
    #[allow(clippy::too_many_arguments)]
    pub fn add_class_row(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str, // e.g., "src/foo.py:ClassName"
        complexity: u32,
        real_complexity: u32,
        lineno: u32,
        endline: u32,
    ) {
        self.revision.append_value(revision);
        self.revision_date.append_value(revision_date);
        self.revision_author.append_option(revision_author);
        self.revision_message.append_option(revision_message);
        self.path.append_value(path);
        self.path_type.append_value("class");

        // No raw metrics for classes
        self.loc.append_null();
        self.sloc.append_null();
        self.lloc.append_null();
        self.comments.append_null();
        self.multi.append_null();
        self.blank.append_null();
        self.single_comments.append_null();

        self.complexity.append_value(complexity as f64);
        self.real_complexity.append_value(real_complexity);

        // No halstead for classes
        self.h1.append_null();
        self.h2.append_null();
        self.n1.append_null();
        self.n2.append_null();
        self.vocabulary.append_null();
        self.length.append_null();
        self.volume.append_null();
        self.difficulty.append_null();
        self.effort.append_null();

        self.mi.append_null();
        self.rank.append_null();

        self.lineno.append_value(lineno);
        self.endline.append_value(endline);
        self.is_method.append_null();
        self.classname.append_null();

        self.row_count += 1;
    }

    /// Build a RecordBatch from the accumulated rows.
    pub fn finish(&mut self) -> RecordBatch {
        let schema = Arc::new(metrics_schema());

        let columns: Vec<ArrayRef> = vec![
            Arc::new(self.revision.finish()),
            Arc::new(self.revision_date.finish()),
            Arc::new(self.revision_author.finish()),
            Arc::new(self.revision_message.finish()),
            Arc::new(self.path.finish()),
            Arc::new(self.path_type.finish()),
            Arc::new(self.loc.finish()),
            Arc::new(self.sloc.finish()),
            Arc::new(self.lloc.finish()),
            Arc::new(self.comments.finish()),
            Arc::new(self.multi.finish()),
            Arc::new(self.blank.finish()),
            Arc::new(self.single_comments.finish()),
            Arc::new(self.complexity.finish()),
            Arc::new(self.real_complexity.finish()),
            Arc::new(self.h1.finish()),
            Arc::new(self.h2.finish()),
            Arc::new(self.n1.finish()),
            Arc::new(self.n2.finish()),
            Arc::new(self.vocabulary.finish()),
            Arc::new(self.length.finish()),
            Arc::new(self.volume.finish()),
            Arc::new(self.difficulty.finish()),
            Arc::new(self.effort.finish()),
            Arc::new(self.mi.finish()),
            Arc::new(self.rank.finish()),
            Arc::new(self.lineno.finish()),
            Arc::new(self.endline.finish()),
            Arc::new(self.is_method.finish()),
            Arc::new(self.classname.finish()),
        ];

        RecordBatch::try_new(schema, columns).expect("Failed to create RecordBatch")
    }

    /// Check if the builder has any rows.
    pub fn is_empty(&self) -> bool {
        self.row_count == 0
    }

    /// Add an aggregate row and return it as a MetricRow for state tracking.
    #[allow(clippy::too_many_arguments)]
    pub fn add_aggregate_row_tracked(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str,
        path_type: &str,
        loc: Option<i64>,
        sloc: Option<i64>,
        lloc: Option<i64>,
        comments: Option<i64>,
        multi: Option<i64>,
        blank: Option<i64>,
        single_comments: Option<i64>,
        complexity: Option<f64>,
        h1: Option<i64>,
        h2: Option<i64>,
        n1: Option<i64>,
        n2: Option<i64>,
        vocabulary: Option<i64>,
        length: Option<i64>,
        volume: Option<f64>,
        difficulty: Option<f64>,
        effort: Option<f64>,
        mi: Option<f64>,
        rank: Option<&str>,
    ) -> MetricRow {
        self.add_aggregate_row(
            revision,
            revision_date,
            revision_author,
            revision_message,
            path,
            path_type,
            loc,
            sloc,
            lloc,
            comments,
            multi,
            blank,
            single_comments,
            complexity,
            h1,
            h2,
            n1,
            n2,
            vocabulary,
            length,
            volume,
            difficulty,
            effort,
            mi,
            rank,
        );
        MetricRow {
            revision: revision.to_string(),
            revision_date,
            revision_author: revision_author.map(|s| s.to_string()),
            revision_message: revision_message.map(|s| s.to_string()),
            path: path.to_string(),
            path_type: path_type.to_string(),
            loc,
            sloc,
            lloc,
            comments,
            multi,
            blank,
            single_comments,
            complexity,
            real_complexity: None,
            h1,
            h2,
            n1,
            n2,
            vocabulary,
            length,
            volume,
            difficulty,
            effort,
            mi,
            rank: rank.map(|s| s.to_string()),
            lineno: None,
            endline: None,
            is_method: None,
            classname: None,
        }
    }

    /// Add a function row and return it as a MetricRow for state tracking.
    #[allow(clippy::too_many_arguments)]
    pub fn add_function_row_tracked(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str,
        complexity: u32,
        lineno: u32,
        endline: u32,
        is_method: bool,
        classname: Option<&str>,
        h1: Option<u32>,
        h2: Option<u32>,
        n1: Option<u32>,
        n2: Option<u32>,
        vocabulary: Option<u32>,
        length: Option<u32>,
        volume: Option<f64>,
        difficulty: Option<f64>,
        effort: Option<f64>,
    ) -> MetricRow {
        self.add_function_row(
            revision,
            revision_date,
            revision_author,
            revision_message,
            path,
            complexity,
            lineno,
            endline,
            is_method,
            classname,
            h1,
            h2,
            n1,
            n2,
            vocabulary,
            length,
            volume,
            difficulty,
            effort,
        );
        MetricRow {
            revision: revision.to_string(),
            revision_date,
            revision_author: revision_author.map(|s| s.to_string()),
            revision_message: revision_message.map(|s| s.to_string()),
            path: path.to_string(),
            path_type: "function".to_string(),
            loc: None,
            sloc: None,
            lloc: None,
            comments: None,
            multi: None,
            blank: None,
            single_comments: None,
            complexity: Some(complexity as f64),
            real_complexity: None,
            h1: h1.map(|v| v as i64),
            h2: h2.map(|v| v as i64),
            n1: n1.map(|v| v as i64),
            n2: n2.map(|v| v as i64),
            vocabulary: vocabulary.map(|v| v as i64),
            length: length.map(|v| v as i64),
            volume,
            difficulty,
            effort,
            mi: None,
            rank: None,
            lineno: Some(lineno),
            endline: Some(endline),
            is_method: Some(is_method),
            classname: classname.map(|s| s.to_string()),
        }
    }

    /// Add a class row and return it as a MetricRow for state tracking.
    #[allow(clippy::too_many_arguments)]
    pub fn add_class_row_tracked(
        &mut self,
        revision: &str,
        revision_date: i64,
        revision_author: Option<&str>,
        revision_message: Option<&str>,
        path: &str,
        complexity: u32,
        real_complexity: u32,
        lineno: u32,
        endline: u32,
    ) -> MetricRow {
        self.add_class_row(
            revision,
            revision_date,
            revision_author,
            revision_message,
            path,
            complexity,
            real_complexity,
            lineno,
            endline,
        );
        MetricRow {
            revision: revision.to_string(),
            revision_date,
            revision_author: revision_author.map(|s| s.to_string()),
            revision_message: revision_message.map(|s| s.to_string()),
            path: path.to_string(),
            path_type: "class".to_string(),
            loc: None,
            sloc: None,
            lloc: None,
            comments: None,
            multi: None,
            blank: None,
            single_comments: None,
            complexity: Some(complexity as f64),
            real_complexity: Some(real_complexity),
            h1: None,
            h2: None,
            n1: None,
            n2: None,
            vocabulary: None,
            length: None,
            volume: None,
            difficulty: None,
            effort: None,
            mi: None,
            rank: None,
            lineno: Some(lineno),
            endline: Some(endline),
            is_method: None,
            classname: None,
        }
    }
}

/// Internal state for WilyIndex - holds loaded rows and new rows
struct IndexState {
    /// Rows loaded from existing parquet file
    loaded_rows: Vec<MetricRow>,
    /// New rows added via analyze_revision
    new_rows: Vec<MetricRow>,
    /// Whether we've loaded from disk yet
    loaded: bool,
}

impl IndexState {
    fn new() -> Self {
        Self {
            loaded_rows: Vec::new(),
            new_rows: Vec::new(),
            loaded: false,
        }
    }

    /// Get all rows (loaded + new)
    fn all_rows(&self) -> impl Iterator<Item = &MetricRow> {
        self.loaded_rows.iter().chain(self.new_rows.iter())
    }
}

/// Load rows from a parquet file into MetricRow structs
fn load_rows_from_parquet(path: &str) -> Result<Vec<MetricRow>, String> {
    use arrow::array::{Array, AsArray, BooleanArray};
    use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
    use std::path::Path;

    let file_path = Path::new(path);
    if !file_path.exists() {
        return Ok(Vec::new());
    }

    let file = File::open(path).map_err(|e| format!("Failed to open file: {}", e))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|e| format!("Failed to read parquet: {}", e))?;
    let reader = builder
        .build()
        .map_err(|e| format!("Failed to build reader: {}", e))?;

    let mut rows = Vec::new();

    for batch_result in reader {
        let batch = batch_result.map_err(|e| format!("Failed to read batch: {}", e))?;

        let revision_col = batch.column(0).as_string::<i32>();
        let revision_date_col = batch
            .column(1)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let revision_author_col = batch.column(2).as_string::<i32>();
        let revision_message_col = batch.column(3).as_string::<i32>();
        let path_col = batch.column(4).as_string::<i32>();
        let path_type_col = batch.column(5).as_string::<i32>();
        let loc_col = batch
            .column(6)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let sloc_col = batch
            .column(7)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let lloc_col = batch
            .column(8)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let comments_col = batch
            .column(9)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let multi_col = batch
            .column(10)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let blank_col = batch
            .column(11)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let single_comments_col = batch
            .column(12)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let complexity_col = batch
            .column(13)
            .as_primitive::<arrow::datatypes::Float64Type>();
        let real_complexity_col = batch
            .column(14)
            .as_primitive::<arrow::datatypes::UInt32Type>();
        let h1_col = batch
            .column(15)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let h2_col = batch
            .column(16)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let n1_col = batch
            .column(17)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let n2_col = batch
            .column(18)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let vocabulary_col = batch
            .column(19)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let length_col = batch
            .column(20)
            .as_primitive::<arrow::datatypes::Int64Type>();
        let volume_col = batch
            .column(21)
            .as_primitive::<arrow::datatypes::Float64Type>();
        let difficulty_col = batch
            .column(22)
            .as_primitive::<arrow::datatypes::Float64Type>();
        let effort_col = batch
            .column(23)
            .as_primitive::<arrow::datatypes::Float64Type>();
        let mi_col = batch
            .column(24)
            .as_primitive::<arrow::datatypes::Float64Type>();
        let rank_col = batch.column(25).as_string::<i32>();
        let lineno_col = batch
            .column(26)
            .as_primitive::<arrow::datatypes::UInt32Type>();
        let endline_col = batch
            .column(27)
            .as_primitive::<arrow::datatypes::UInt32Type>();
        let is_method_col = batch
            .column(28)
            .as_any()
            .downcast_ref::<BooleanArray>()
            .unwrap();
        let classname_col = batch.column(29).as_string::<i32>();

        for i in 0..batch.num_rows() {
            let row = MetricRow {
                revision: revision_col.value(i).to_string(),
                revision_date: revision_date_col.value(i),
                revision_author: if revision_author_col.is_null(i) {
                    None
                } else {
                    Some(revision_author_col.value(i).to_string())
                },
                revision_message: if revision_message_col.is_null(i) {
                    None
                } else {
                    Some(revision_message_col.value(i).to_string())
                },
                path: path_col.value(i).to_string(),
                path_type: path_type_col.value(i).to_string(),
                loc: if loc_col.is_null(i) {
                    None
                } else {
                    Some(loc_col.value(i))
                },
                sloc: if sloc_col.is_null(i) {
                    None
                } else {
                    Some(sloc_col.value(i))
                },
                lloc: if lloc_col.is_null(i) {
                    None
                } else {
                    Some(lloc_col.value(i))
                },
                comments: if comments_col.is_null(i) {
                    None
                } else {
                    Some(comments_col.value(i))
                },
                multi: if multi_col.is_null(i) {
                    None
                } else {
                    Some(multi_col.value(i))
                },
                blank: if blank_col.is_null(i) {
                    None
                } else {
                    Some(blank_col.value(i))
                },
                single_comments: if single_comments_col.is_null(i) {
                    None
                } else {
                    Some(single_comments_col.value(i))
                },
                complexity: if complexity_col.is_null(i) {
                    None
                } else {
                    Some(complexity_col.value(i))
                },
                real_complexity: if real_complexity_col.is_null(i) {
                    None
                } else {
                    Some(real_complexity_col.value(i))
                },
                h1: if h1_col.is_null(i) {
                    None
                } else {
                    Some(h1_col.value(i))
                },
                h2: if h2_col.is_null(i) {
                    None
                } else {
                    Some(h2_col.value(i))
                },
                n1: if n1_col.is_null(i) {
                    None
                } else {
                    Some(n1_col.value(i))
                },
                n2: if n2_col.is_null(i) {
                    None
                } else {
                    Some(n2_col.value(i))
                },
                vocabulary: if vocabulary_col.is_null(i) {
                    None
                } else {
                    Some(vocabulary_col.value(i))
                },
                length: if length_col.is_null(i) {
                    None
                } else {
                    Some(length_col.value(i))
                },
                volume: if volume_col.is_null(i) {
                    None
                } else {
                    Some(volume_col.value(i))
                },
                difficulty: if difficulty_col.is_null(i) {
                    None
                } else {
                    Some(difficulty_col.value(i))
                },
                effort: if effort_col.is_null(i) {
                    None
                } else {
                    Some(effort_col.value(i))
                },
                mi: if mi_col.is_null(i) {
                    None
                } else {
                    Some(mi_col.value(i))
                },
                rank: if rank_col.is_null(i) {
                    None
                } else {
                    Some(rank_col.value(i).to_string())
                },
                lineno: if lineno_col.is_null(i) {
                    None
                } else {
                    Some(lineno_col.value(i))
                },
                endline: if endline_col.is_null(i) {
                    None
                } else {
                    Some(endline_col.value(i))
                },
                is_method: if is_method_col.is_null(i) {
                    None
                } else {
                    Some(is_method_col.value(i))
                },
                classname: if classname_col.is_null(i) {
                    None
                } else {
                    Some(classname_col.value(i).to_string())
                },
            };
            rows.push(row);
        }
    }

    Ok(rows)
}

/// Python context manager for efficient multi-revision parquet writes and reads.
///
/// Usage for writing:
/// ```python
/// with WilyIndex(path, operators) as index:
///     index.analyze_revision(paths, base_path, revision_key, ...)
///     index.analyze_revision(paths, base_path, revision_key, ...)
/// # File is written on exit
/// ```
///
/// Usage for reading:
/// ```python
/// with WilyIndex(path) as index:
///     rows = index["src/foo.py"]  # Get all rows for a path
///     for row in index:           # Iterate all rows
///         print(row)
/// ```
#[pyclass]
pub struct WilyIndex {
    output_path: String,
    builder: Mutex<MetricsBuilder>,
    state: Mutex<IndexState>,
    operators: Vec<String>,
}

#[pymethods]
impl WilyIndex {
    #[new]
    #[pyo3(signature = (output_path, operators=None))]
    fn new(output_path: String, operators: Option<Vec<String>>) -> Self {
        Self {
            output_path,
            builder: Mutex::new(MetricsBuilder::new()),
            state: Mutex::new(IndexState::new()),
            operators: operators.unwrap_or_default(),
        }
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyResult<PyRef<'_, Self>> {
        // Lazily load existing data on enter
        {
            let mut state = slf.state.lock().map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
            })?;
            if !state.loaded {
                state.loaded_rows = load_rows_from_parquet(&slf.output_path)
                    .map_err(PyErr::new::<pyo3::exceptions::PyIOError, _>)?;
                state.loaded = true;
            }
        }
        Ok(slf)
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        &self,
        _exc_type: Option<Bound<'_, pyo3::types::PyAny>>,
        _exc_val: Option<Bound<'_, pyo3::types::PyAny>>,
        _exc_tb: Option<Bound<'_, pyo3::types::PyAny>>,
    ) -> PyResult<bool> {
        // Write accumulated data to parquet
        let mut builder = self.builder.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;

        if builder.is_empty() {
            // Nothing to write
            return Ok(false);
        }

        let batch = builder.finish();
        append_parquet(&self.output_path, batch)
            .map_err(PyErr::new::<pyo3::exceptions::PyIOError, _>)?;

        Ok(false) // Don't suppress exceptions
    }

    /// Get all rows matching a path (file path or path prefix).
    /// Returns rows where the path equals or starts with the given path.
    /// Rows are sorted by revision_date descending (newest first).
    fn __getitem__(&self, py: Python<'_>, path: String) -> PyResult<Py<PyList>> {
        let state = self.state.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;
        // TODO: Decide if we want to filter by path_type as well
        let mut matching_rows: Vec<_> = state
            .all_rows()
            .filter(|row| row.path == path)
            .cloned()
            .collect();

        // Sort by revision_date ascending (newest last)
        matching_rows.sort_by(|a, b| a.revision_date.cmp(&b.revision_date));

        // TODO: There is a more pragmatic way to do this, using PyList::new(py, enumerables)
        let list = PyList::empty(py);
        for row in matching_rows {
            list.append(row.to_py_dict(py)?)?;
        }
        Ok(list.into())
    }

    /// Iterate over all rows in the index.
    fn __iter__(slf: PyRef<'_, Self>) -> PyResult<WilyIndexIterator> {
        let state = slf.state.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;

        // Collect all rows into a vec for the iterator
        let all_rows: Vec<MetricRow> = state.all_rows().cloned().collect();
        Ok(WilyIndexIterator {
            rows: all_rows,
            index: 0,
        })
    }

    /// Get the number of rows in the index.
    fn __len__(&self) -> PyResult<usize> {
        let state = self.state.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;
        Ok(state.loaded_rows.len() + state.new_rows.len())
    }

    /// Analyze a revision and accumulate results.
    ///
    /// # Arguments
    /// * `paths` - List of absolute file paths to analyze
    /// * `base_path` - Base path for computing relative paths
    /// * `revision_key` - Commit hash or revision identifier
    /// * `revision_date` - Unix timestamp of the revision
    /// * `revision_author` - Author name (optional)
    /// * `revision_message` - Commit message (optional)
    ///
    /// # Returns
    /// Root LOC for this revision
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (paths, base_path, revision_key, revision_date, revision_author, revision_message))]
    fn analyze_revision(
        &self,
        py: Python<'_>,
        paths: Vec<String>,
        base_path: String,
        revision_key: String,
        revision_date: i64,
        revision_author: Option<String>,
        revision_message: Option<String>,
    ) -> PyResult<i64> {
        use crate::cyclomatic;
        use crate::halstead;
        use crate::maintainability;
        use crate::raw;
        use rayon::prelude::*;
        use std::collections::{HashMap, HashSet};
        use std::fs;

        let operators = &self.operators;
        let include_raw = operators.iter().any(|o| o == "raw");
        let include_cyclomatic = operators.iter().any(|o| o == "cyclomatic");
        let include_halstead = operators.iter().any(|o| o == "halstead");
        let include_maintainability = operators.iter().any(|o| o == "maintainability");

        // Compute relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                if p.starts_with(&base_path) {
                    let rel = p[base_path.len()..].trim_start_matches('/');
                    rel.to_string()
                } else {
                    p.to_string()
                }
            })
            .collect();

        // Collect all directory paths for aggregation
        let directories: HashSet<String> = relative_paths
            .iter()
            .flat_map(|p| get_parent_paths(p))
            .collect();

        let base_path_buf = PathBuf::from(base_path);

        // Analysis result for a single file
        struct FileResult {
            rel_path: String,
            raw: Option<HashMap<String, i64>>,
            cyclomatic_total: Option<i64>,
            cyclomatic_functions: Vec<(String, u32, u32, u32, bool, Option<String>)>,
            cyclomatic_classes: Vec<(String, u32, u32, u32, u32)>,
            halstead_total: Option<HalsteadTotals>,
            halstead_functions: Vec<HalsteadFunctionMetrics>,
            mi: Option<(f64, String)>,
        }

        // Phase 1: Parallel file analysis
        let file_results: Vec<FileResult> = py.detach(|| {
            paths
                .par_iter()
                .filter_map(|rel_path| {
                    let abs_path = base_path_buf.join(rel_path);
                    let content = fs::read_to_string(abs_path).ok()?;
                    let raw = if include_raw {
                        Some(raw::analyze_source_raw(&content))
                    } else {
                        None
                    };

                    let (cyclomatic_total, cyclomatic_functions, cyclomatic_classes) =
                        if include_cyclomatic {
                            match cyclomatic::analyze_source_full(&content) {
                                Ok((functions, classes, line_index)) => {
                                    let mut total: i64 = 0;
                                    let funcs: Vec<_> = functions
                                        .iter()
                                        .map(|f| {
                                            let lineno = ruff_source_file::LineIndex::line_index(
                                                &line_index,
                                                ruff_text_size::TextSize::new(f.start_offset),
                                            );
                                            let endline = ruff_source_file::LineIndex::line_index(
                                                &line_index,
                                                ruff_text_size::TextSize::new(f.end_offset),
                                            );
                                            total += f.complexity as i64;
                                            (
                                                f.fullname(),
                                                f.complexity,
                                                (lineno.to_zero_indexed() + 1) as u32,
                                                (endline.to_zero_indexed() + 1) as u32,
                                                f.is_method,
                                                f.classname.clone(),
                                            )
                                        })
                                        .collect();
                                    let cls: Vec<_> = classes
                                        .iter()
                                        .map(|c| {
                                            let lineno = ruff_source_file::LineIndex::line_index(
                                                &line_index,
                                                ruff_text_size::TextSize::new(c.start_offset),
                                            );
                                            let endline = ruff_source_file::LineIndex::line_index(
                                                &line_index,
                                                ruff_text_size::TextSize::new(c.end_offset),
                                            );
                                            total += c.complexity() as i64;
                                            (
                                                c.name.clone(),
                                                c.complexity(),
                                                c.real_complexity,
                                                (lineno.to_zero_indexed() + 1) as u32,
                                                (endline.to_zero_indexed() + 1) as u32,
                                            )
                                        })
                                        .collect();
                                    (Some(total), funcs, cls)
                                }
                                Err(_) => (Some(0), Vec::new(), Vec::new()),
                            }
                        } else {
                            (None, Vec::new(), Vec::new())
                        };

                    let (halstead_total, halstead_functions) = if include_halstead {
                        match halstead::analyze_source_full(&content) {
                            Ok((functions, total, line_index)) => {
                                let total_metrics = (
                                    total.h1(),
                                    total.h2(),
                                    total.n1(),
                                    total.n2(),
                                    total.vocabulary(),
                                    total.length(),
                                    total.volume(),
                                    total.difficulty(),
                                    total.effort(),
                                );
                                let funcs: Vec<_> = functions
                                    .iter()
                                    .map(|f| {
                                        let lineno = ruff_source_file::LineIndex::line_index(
                                            &line_index,
                                            ruff_text_size::TextSize::new(f.start_offset),
                                        );
                                        let endline = ruff_source_file::LineIndex::line_index(
                                            &line_index,
                                            ruff_text_size::TextSize::new(f.end_offset),
                                        );
                                        (
                                            f.name.clone(),
                                            f.metrics.h1(),
                                            f.metrics.h2(),
                                            f.metrics.n1(),
                                            f.metrics.n2(),
                                            f.metrics.vocabulary(),
                                            f.metrics.length(),
                                            f.metrics.volume(),
                                            f.metrics.difficulty(),
                                            f.metrics.effort(),
                                            (lineno.to_zero_indexed() + 1) as u32,
                                            (endline.to_zero_indexed() + 1) as u32,
                                        )
                                    })
                                    .collect();
                                (Some(total_metrics), funcs)
                            }
                            Err(_) => (Some((0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)), Vec::new()),
                        }
                    } else {
                        (None, Vec::new())
                    };

                    let mi = if include_maintainability {
                        let (mi_val, rank) = maintainability::analyze_source_mi(&content);
                        Some((mi_val, rank))
                    } else {
                        None
                    };

                    Some(FileResult {
                        rel_path: rel_path.clone(),
                        raw,
                        cyclomatic_total,
                        cyclomatic_functions,
                        cyclomatic_classes,
                        halstead_total,
                        halstead_functions,
                        mi,
                    })
                })
                .collect()
        });

        // Phase 2: Build parquet rows (single-threaded, with lock)
        let mut builder = self.builder.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;
        let mut state = self.state.lock().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock poisoned: {}", e))
        })?;
        let rev_author = revision_author.as_deref();
        let rev_message = revision_message.as_deref();

        // Aggregate metrics by directory
        let mut dir_raw: std::collections::HashMap<String, std::collections::HashMap<String, i64>> =
            std::collections::HashMap::new();
        let mut dir_complexity: std::collections::HashMap<String, Vec<i64>> =
            std::collections::HashMap::new();
        let mut dir_halstead: std::collections::HashMap<String, Vec<HalsteadTotals>> =
            std::collections::HashMap::new();
        let mut dir_mi: std::collections::HashMap<String, Vec<(f64, String)>> =
            std::collections::HashMap::new();

        // Add file rows and collect for aggregation
        for result in &file_results {
            // Add file-level row
            let raw_metrics = result.raw.as_ref();
            let row = builder.add_aggregate_row_tracked(
                &revision_key,
                revision_date,
                rev_author,
                rev_message,
                &result.rel_path,
                "file",
                raw_metrics.and_then(|r| r.get("loc").copied()),
                raw_metrics.and_then(|r| r.get("sloc").copied()),
                raw_metrics.and_then(|r| r.get("lloc").copied()),
                raw_metrics.and_then(|r| r.get("comments").copied()),
                raw_metrics.and_then(|r| r.get("multi").copied()),
                raw_metrics.and_then(|r| r.get("blank").copied()),
                raw_metrics.and_then(|r| r.get("single_comments").copied()),
                result.cyclomatic_total.map(|c| c as f64),
                result.halstead_total.map(|h| h.0 as i64),
                result.halstead_total.map(|h| h.1 as i64),
                result.halstead_total.map(|h| h.2 as i64),
                result.halstead_total.map(|h| h.3 as i64),
                result.halstead_total.map(|h| h.4 as i64),
                result.halstead_total.map(|h| h.5 as i64),
                result.halstead_total.map(|h| h.6),
                result.halstead_total.map(|h| h.7),
                result.halstead_total.map(|h| h.8),
                result.mi.as_ref().map(|(mi, _)| *mi),
                result.mi.as_ref().map(|(_, r)| r.as_str()),
            );
            state.new_rows.push(row);

            // Add function rows
            for (name, complexity, lineno, endline, is_method, classname) in
                &result.cyclomatic_functions
            {
                let func_path = format!("{}:{}", result.rel_path, name);
                // Find matching halstead data if available
                let hal = result.halstead_functions.iter().find(|(n, ..)| n == name);
                let row = builder.add_function_row_tracked(
                    &revision_key,
                    revision_date,
                    rev_author,
                    rev_message,
                    &func_path,
                    *complexity,
                    *lineno,
                    *endline,
                    *is_method,
                    classname.as_deref(),
                    hal.map(|h| h.1),
                    hal.map(|h| h.2),
                    hal.map(|h| h.3),
                    hal.map(|h| h.4),
                    hal.map(|h| h.5),
                    hal.map(|h| h.6),
                    hal.map(|h| h.7),
                    hal.map(|h| h.8),
                    hal.map(|h| h.9),
                );
                state.new_rows.push(row);
            }

            // Add class rows
            for (name, complexity, real_complexity, lineno, endline) in &result.cyclomatic_classes {
                let class_path = format!("{}:{}", result.rel_path, name);
                let row = builder.add_class_row_tracked(
                    &revision_key,
                    revision_date,
                    rev_author,
                    rev_message,
                    &class_path,
                    *complexity,
                    *real_complexity,
                    *lineno,
                    *endline,
                );
                state.new_rows.push(row);
            }

            // Collect for directory aggregation
            for dir in get_parent_paths(&result.rel_path) {
                if let Some(raw) = &result.raw {
                    let entry = dir_raw.entry(dir.clone()).or_default();
                    for (k, v) in raw {
                        *entry.entry(k.clone()).or_insert(0) += v;
                    }
                }
                if let Some(cc) = result.cyclomatic_total {
                    dir_complexity.entry(dir.clone()).or_default().push(cc);
                }
                if let Some(hal) = result.halstead_total {
                    dir_halstead.entry(dir.clone()).or_default().push(hal);
                }
                if let Some(mi) = &result.mi {
                    dir_mi.entry(dir.clone()).or_default().push(mi.clone());
                }
            }
        }

        // Add directory aggregate rows
        for dir in &directories {
            let path_type = if dir.is_empty() { "root" } else { "directory" };
            let raw = dir_raw.get(dir);
            let complexities = dir_complexity.get(dir);
            let halsteads = dir_halstead.get(dir);
            let mis = dir_mi.get(dir);

            // Compute aggregates
            let mean_complexity = complexities.map(|v| {
                if v.is_empty() {
                    0.0
                } else {
                    v.iter().sum::<i64>() as f64 / v.len() as f64
                }
            });

            let sum_halstead = halsteads.map(|v| {
                v.iter().fold(
                    (0i64, 0i64, 0i64, 0i64, 0i64, 0i64, 0.0, 0.0, 0.0),
                    |acc, h| {
                        (
                            acc.0 + h.0 as i64,
                            acc.1 + h.1 as i64,
                            acc.2 + h.2 as i64,
                            acc.3 + h.3 as i64,
                            acc.4 + h.4 as i64,
                            acc.5 + h.5 as i64,
                            acc.6 + h.6,
                            acc.7 + h.7,
                            acc.8 + h.8,
                        )
                    },
                )
            });

            let (mean_mi, mode_rank) = if let Some(v) = mis {
                if v.is_empty() {
                    (None, None)
                } else {
                    let mean = v.iter().map(|(mi, _)| mi).sum::<f64>() / v.len() as f64;
                    // Mode of ranks
                    let mut rank_counts: HashMap<&str, usize> = HashMap::new();
                    for (_, r) in v {
                        *rank_counts.entry(r.as_str()).or_insert(0) += 1;
                    }
                    let mode = rank_counts
                        .into_iter()
                        .max_by_key(|(_, c)| *c)
                        .map(|(r, _)| r.to_string());
                    (Some(mean), mode)
                }
            } else {
                (None, None)
            };

            let row = builder.add_aggregate_row_tracked(
                &revision_key,
                revision_date,
                rev_author,
                rev_message,
                dir,
                path_type,
                raw.and_then(|r| r.get("loc").copied()),
                raw.and_then(|r| r.get("sloc").copied()),
                raw.and_then(|r| r.get("lloc").copied()),
                raw.and_then(|r| r.get("comments").copied()),
                raw.and_then(|r| r.get("multi").copied()),
                raw.and_then(|r| r.get("blank").copied()),
                raw.and_then(|r| r.get("single_comments").copied()),
                mean_complexity,
                sum_halstead.map(|h| h.0),
                sum_halstead.map(|h| h.1),
                sum_halstead.map(|h| h.2),
                sum_halstead.map(|h| h.3),
                sum_halstead.map(|h| h.4),
                sum_halstead.map(|h| h.5),
                sum_halstead.map(|h| h.6),
                sum_halstead.map(|h| h.7),
                sum_halstead.map(|h| h.8),
                mean_mi,
                mode_rank.as_deref(),
            );
            state.new_rows.push(row);
        }

        // Get root LOC
        let root_loc = dir_raw
            .get("")
            .and_then(|r| r.get("loc").copied())
            .unwrap_or(0);

        Ok(root_loc)
    }
}

/// Write a RecordBatch to a new parquet file.
pub fn write_parquet(path: &str, batch: RecordBatch) -> Result<(), String> {
    let file = File::create(path).map_err(|e| format!("Failed to create file: {}", e))?;

    let props = WriterProperties::builder()
        .set_compression(Compression::LZ4_RAW)
        .build();

    let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(props))
        .map_err(|e| format!("Failed to create parquet writer: {}", e))?;

    writer
        .write(&batch)
        .map_err(|e| format!("Failed to write batch: {}", e))?;

    writer
        .close()
        .map_err(|e| format!("Failed to close writer: {}", e))?;

    Ok(())
}

/// Append a RecordBatch to an existing parquet file by reading it, appending, and rewriting.
/// For large files, consider using a different strategy (e.g., multiple row groups).
pub fn append_parquet(path: &str, new_batch: RecordBatch) -> Result<(), String> {
    use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
    use std::path::Path;

    let file_path = Path::new(path);

    if !file_path.exists() {
        // File doesn't exist, just write new batch
        return write_parquet(path, new_batch);
    }

    // Read existing data
    let file = File::open(path).map_err(|e| format!("Failed to open file: {}", e))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|e| format!("Failed to read parquet: {}", e))?;
    let reader = builder
        .build()
        .map_err(|e| format!("Failed to build reader: {}", e))?;

    let mut batches: Vec<RecordBatch> = reader
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to read batches: {}", e))?;

    // Append new batch
    batches.push(new_batch);

    // Concatenate all batches
    let combined = arrow::compute::concat_batches(&batches[0].schema(), &batches)
        .map_err(|e| format!("Failed to concat batches: {}", e))?;

    // Write combined data
    write_parquet(path, combined)
}

/// Python-exposed function to get the parquet schema as a list of (name, type) tuples.
#[pyfunction]
pub fn get_metrics_schema() -> Vec<(String, String)> {
    metrics_schema()
        .fields()
        .iter()
        .map(|f| (f.name().clone(), format!("{:?}", f.data_type())))
        .collect()
}

/// Iterator for WilyIndex rows.
#[pyclass]
pub struct WilyIndexIterator {
    rows: Vec<MetricRow>,
    index: usize,
}

#[pymethods]
impl WilyIndexIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Py<PyDict>>> {
        if self.index < self.rows.len() {
            let row = &self.rows[self.index];
            self.index += 1;
            Ok(Some(row.to_py_dict(py)?))
        } else {
            Ok(None)
        }
    }
}

pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(get_metrics_schema, parent_module)?)?;
    parent_module.add_class::<WilyIndex>()?;
    parent_module.add_class::<WilyIndexIterator>()?;
    Ok(())
}
