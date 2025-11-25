//! Maintainability Index calculation using Ruff's AST.
//!
//! The Maintainability Index (MI) is computed from:
//! - Halstead Volume
//! - Cyclomatic Complexity
//! - Logical Lines of Code (LLOC)
//! - Percentage of comment lines
//!
//! Formula (normalized 0-100):
//! MI = max(0, min(100, (171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LLOC) + 50*sin(sqrt(2.46*radians(CM)))) * 100/171))

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};
use ruff_python_ast::{self as ast, Stmt, visitor::{self, Visitor}};
use ruff_python_parser::parse_module;
use std::collections::HashSet;

/// Raw metrics needed for MI calculation
#[derive(Debug, Clone, Default)]
struct RawMetrics {
    lloc: u32,
    sloc: u32,
    comments: u32,
    multi: u32,
}

/// Halstead metrics needed for MI calculation
#[derive(Debug, Clone, Default)]
struct HalsteadMetrics {
    operators_seen: HashSet<String>,
    operands_seen: HashSet<String>,
    operators: u32,
    operands: u32,
}

impl HalsteadMetrics {
    fn h1(&self) -> u32 {
        self.operators_seen.len() as u32
    }

    fn h2(&self) -> u32 {
        self.operands_seen.len() as u32
    }

    fn vocabulary(&self) -> u32 {
        self.h1() + self.h2()
    }

    fn length(&self) -> u32 {
        self.operators + self.operands
    }

    fn volume(&self) -> f64 {
        let vocab = self.vocabulary();
        if vocab == 0 {
            return 0.0;
        }
        self.length() as f64 * (vocab as f64).log2()
    }
}

/// Cyclomatic complexity counter
struct ComplexityVisitor {
    complexity: u32,
}

impl ComplexityVisitor {
    fn new() -> Self {
        Self { complexity: 0 }
    }
}

impl<'a> Visitor<'a> for ComplexityVisitor {
    fn visit_stmt(&mut self, stmt: &'a Stmt) {
        match stmt {
            Stmt::If(node) => {
                self.complexity += 1;
                // Count elif clauses
                for clause in &node.elif_else_clauses {
                    if clause.test.is_some() {
                        self.complexity += 1;
                    }
                }
            }
            Stmt::For(_) | Stmt::While(_) => {
                self.complexity += 1;
            }
            Stmt::Try(node) => {
                // Each except handler adds complexity
                self.complexity += node.handlers.len() as u32;
            }
            Stmt::With(node) => {
                self.complexity += node.items.len() as u32;
            }
            _ => {}
        }
        visitor::walk_stmt(self, stmt);
    }

    fn visit_expr(&mut self, expr: &'a ast::Expr) {
        match expr {
            ast::Expr::BoolOp(node) => {
                // Each boolean operator (and/or) adds complexity
                // For n values, there are n-1 operators
                self.complexity += (node.values.len() - 1) as u32;
            }
            ast::Expr::If(_) => {
                // Ternary/conditional expression
                self.complexity += 1;
            }
            ast::Expr::ListComp(node) => {
                for gen in &node.generators {
                    self.complexity += 1; // for
                    self.complexity += gen.ifs.len() as u32; // if clauses
                }
            }
            ast::Expr::SetComp(node) => {
                for gen in &node.generators {
                    self.complexity += 1;
                    self.complexity += gen.ifs.len() as u32;
                }
            }
            ast::Expr::DictComp(node) => {
                for gen in &node.generators {
                    self.complexity += 1;
                    self.complexity += gen.ifs.len() as u32;
                }
            }
            ast::Expr::Generator(node) => {
                for gen in &node.generators {
                    self.complexity += 1;
                    self.complexity += gen.ifs.len() as u32;
                }
            }
            _ => {}
        }
        visitor::walk_expr(self, expr);
    }
}

/// Halstead visitor that counts operators and operands
struct HalsteadVisitor {
    metrics: HalsteadMetrics,
}

impl HalsteadVisitor {
    fn new() -> Self {
        Self {
            metrics: HalsteadMetrics::default(),
        }
    }

    fn add_operator(&mut self, op_name: &str) {
        self.metrics.operators += 1;
        self.metrics.operators_seen.insert(op_name.to_string());
    }

    fn add_operand(&mut self, operand: &str) {
        self.metrics.operands += 1;
        self.metrics.operands_seen.insert(operand.to_string());
    }

    fn binop_name(op: &ast::Operator) -> &'static str {
        match op {
            ast::Operator::Add => "Add",
            ast::Operator::Sub => "Sub",
            ast::Operator::Mult => "Mult",
            ast::Operator::MatMult => "MatMult",
            ast::Operator::Div => "Div",
            ast::Operator::Mod => "Mod",
            ast::Operator::Pow => "Pow",
            ast::Operator::LShift => "LShift",
            ast::Operator::RShift => "RShift",
            ast::Operator::BitOr => "BitOr",
            ast::Operator::BitXor => "BitXor",
            ast::Operator::BitAnd => "BitAnd",
            ast::Operator::FloorDiv => "FloorDiv",
        }
    }

    fn unaryop_name(op: &ast::UnaryOp) -> &'static str {
        match op {
            ast::UnaryOp::Invert => "Invert",
            ast::UnaryOp::Not => "Not",
            ast::UnaryOp::UAdd => "UAdd",
            ast::UnaryOp::USub => "USub",
        }
    }

    fn boolop_name(op: &ast::BoolOp) -> &'static str {
        match op {
            ast::BoolOp::And => "And",
            ast::BoolOp::Or => "Or",
        }
    }

    fn cmpop_name(op: &ast::CmpOp) -> &'static str {
        match op {
            ast::CmpOp::Eq => "Eq",
            ast::CmpOp::NotEq => "NotEq",
            ast::CmpOp::Lt => "Lt",
            ast::CmpOp::LtE => "LtE",
            ast::CmpOp::Gt => "Gt",
            ast::CmpOp::GtE => "GtE",
            ast::CmpOp::Is => "Is",
            ast::CmpOp::IsNot => "IsNot",
            ast::CmpOp::In => "In",
            ast::CmpOp::NotIn => "NotIn",
        }
    }

    fn expr_to_operand(expr: &ast::Expr) -> String {
        match expr {
            ast::Expr::Name(n) => n.id.to_string(),
            ast::Expr::NumberLiteral(n) => {
                match &n.value {
                    ast::Number::Int(i) => i.to_string(),
                    ast::Number::Float(f) => f.to_string(),
                    ast::Number::Complex { real, imag } => format!("{}+{}j", real, imag),
                }
            }
            ast::Expr::StringLiteral(s) => format!("{:?}", s.value.to_str()),
            ast::Expr::BooleanLiteral(b) => b.value.to_string(),
            ast::Expr::NoneLiteral(_) => "None".to_string(),
            ast::Expr::Attribute(a) => a.attr.to_string(),
            _ => format!("{:?}", expr),
        }
    }
}

impl<'a> Visitor<'a> for HalsteadVisitor {
    fn visit_stmt(&mut self, stmt: &'a Stmt) {
        if let Stmt::AugAssign(node) = stmt {
            self.add_operator(Self::binop_name(&node.op));
            self.add_operand(&Self::expr_to_operand(&node.target));
            self.add_operand(&Self::expr_to_operand(&node.value));
        }
        visitor::walk_stmt(self, stmt);
    }

    fn visit_expr(&mut self, expr: &'a ast::Expr) {
        match expr {
            ast::Expr::BinOp(node) => {
                self.add_operator(Self::binop_name(&node.op));
                self.add_operand(&Self::expr_to_operand(&node.left));
                self.add_operand(&Self::expr_to_operand(&node.right));
            }
            ast::Expr::UnaryOp(node) => {
                self.add_operator(Self::unaryop_name(&node.op));
                self.add_operand(&Self::expr_to_operand(&node.operand));
            }
            ast::Expr::BoolOp(node) => {
                self.add_operator(Self::boolop_name(&node.op));
                for value in &node.values {
                    // For MI calculation, we use simple operand extraction (not the full expr repr)
                    self.add_operand(&Self::expr_to_operand(value));
                }
            }
            ast::Expr::Compare(node) => {
                for op in &node.ops {
                    self.add_operator(Self::cmpop_name(op));
                }
                self.add_operand(&Self::expr_to_operand(&node.left));
                for comp in &node.comparators {
                    self.add_operand(&Self::expr_to_operand(comp));
                }
            }
            _ => {}
        }
        visitor::walk_expr(self, expr);
    }
}

/// Calculate raw metrics from source
fn calculate_raw_metrics(source: &str) -> RawMetrics {
    let mut metrics = RawMetrics::default();
    let mut in_multiline_string = false;
    let mut multiline_quote: Option<&str> = None;

    for line in source.lines() {
        let trimmed = line.trim();

        // Skip empty lines for SLOC
        if trimmed.is_empty() {
            continue;
        }

        // Check for multiline string boundaries
        if in_multiline_string {
            metrics.multi += 1;
            if let Some(quote) = multiline_quote {
                if trimmed.contains(quote) {
                    in_multiline_string = false;
                    multiline_quote = None;
                }
            }
            continue;
        }

        // Check for start of multiline string
        if trimmed.starts_with("\"\"\"") || trimmed.starts_with("'''") {
            let quote = if trimmed.starts_with("\"\"\"") { "\"\"\"" } else { "'''" };
            // Check if it ends on the same line
            if trimmed.len() > 3 && trimmed[3..].contains(quote) {
                metrics.multi += 1;
            } else {
                in_multiline_string = true;
                multiline_quote = Some(quote);
                metrics.multi += 1;
            }
            continue;
        }

        // Check for comments
        if trimmed.starts_with('#') {
            metrics.comments += 1;
            continue;
        }

        // SLOC: non-blank, non-comment lines
        metrics.sloc += 1;

        // LLOC: lines with actual code (simplified - count lines with statements)
        // This is a simplification; proper LLOC requires parsing
        if !trimmed.is_empty() && !trimmed.starts_with('#') {
            metrics.lloc += 1;
        }
    }

    metrics
}

/// Compute the Maintainability Index
fn mi_compute(halstead_volume: f64, complexity: u32, lloc: u32, comments_percent: f64) -> f64 {
    if halstead_volume <= 0.0 || lloc == 0 {
        return 100.0;
    }

    let lloc_f = lloc as f64;
    let complexity_f = complexity as f64;

    let sloc_scale = lloc_f.ln();
    let volume_scale = halstead_volume.ln();
    let comments_scale = (2.46 * comments_percent.to_radians()).sqrt();

    // Non-normalized MI
    let nn_mi = 171.0
        - 5.2 * volume_scale
        - 0.23 * complexity_f
        - 16.2 * sloc_scale
        + 50.0 * comments_scale.sin();

    // Normalize to 0-100
    (nn_mi * 100.0 / 171.0).clamp(0.0, 100.0)
}

/// Compute the MI rank (A, B, or C)
fn mi_rank(score: f64) -> char {
    if score > 19.0 {
        'A'
    } else if score > 9.0 {
        'B'
    } else {
        'C'
    }
}

/// Analyze source code and return MI metrics
fn analyze_source(source: &str, multi: bool) -> Result<(f64, char), String> {
    let parsed = parse_module(source).map_err(|e| e.to_string())?;

    // Calculate raw metrics
    let raw = calculate_raw_metrics(source);

    // Calculate comment percentage
    let comment_lines = raw.comments + if multi { raw.multi } else { 0 };
    let comments_percent = if raw.sloc > 0 {
        (comment_lines as f64 / raw.sloc as f64) * 100.0
    } else {
        0.0
    };

    // Calculate Halstead volume
    let mut halstead = HalsteadVisitor::new();
    for stmt in parsed.suite() {
        halstead.visit_stmt(stmt);
    }
    let volume = halstead.metrics.volume();

    // Calculate cyclomatic complexity
    let mut complexity = ComplexityVisitor::new();
    for stmt in parsed.suite() {
        complexity.visit_stmt(stmt);
    }
    // Base complexity is 1
    let total_complexity = complexity.complexity + 1;

    // Compute MI
    let mi = mi_compute(volume, total_complexity, raw.lloc, comments_percent);
    let rank = mi_rank(mi);

    Ok((mi, rank))
}

/// Public API for parallel module - returns (MI value, rank string).
pub fn analyze_source_mi(source: &str, multi: bool) -> (f64, String) {
    match analyze_source(source, multi) {
        Ok((mi, rank)) => (mi, rank.to_string()),
        Err(_) => (0.0, "C".to_string()),
    }
}

#[pyfunction]
#[pyo3(signature = (entries, multi=true))]
pub fn harvest_maintainability_metrics(
    py: Python<'_>,
    entries: Vec<(String, String)>,
    multi: bool,
) -> PyResult<Vec<(String, Py<PyDict>)>> {
    let mut results = Vec::with_capacity(entries.len());

    for (name, source) in entries {
        let dict = PyDict::new(py);

        match analyze_source(&source, multi) {
            Ok((mi, rank)) => {
                dict.set_item("mi", mi)?;
                dict.set_item("rank", rank.to_string())?;
            }
            Err(err) => {
                dict.set_item("error", err)?;
            }
        }

        results.push((name, dict.unbind()));
    }

    Ok(results)
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(harvest_maintainability_metrics, module)?)?;
    Ok(())
}
