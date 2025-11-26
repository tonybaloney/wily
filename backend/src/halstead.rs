//! Halstead metrics calculation using Ruff's AST.
//!
//! This module calculates Halstead metrics compatible with Radon:
//! - h1: unique operands
//! - h2: unique operators
//! - N1: total operands
//! - N2: total operators
//! - vocabulary: h1 + h2
//! - length: N1 + N2
//! - volume: length * log2(vocabulary)
//! - difficulty: (h2/2) * (N1/h1) - but radon uses a different formula
//! - effort: difficulty * volume
//!
//! Note: Radon's Halstead visitor has some quirks:
//! - For BoolOp, operands are the entire sub-expressions (not leaf values)
//! - AugAssign counts as an operator with target and value as operands

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};
use ruff_python_ast::{
    self as ast,
    visitor::{self, Visitor},
    Expr, Stmt,
};
use ruff_python_parser::parse_module;
use ruff_source_file::LineIndex;
use ruff_text_size::{Ranged, TextSize};
use std::collections::HashSet;

/// Halstead metrics for a code block
#[derive(Debug, Clone, Default)]
pub struct HalsteadMetrics {
    /// Set of unique operators seen
    operators_seen: HashSet<String>,
    /// Set of unique operands seen (context, operand_repr)
    operands_seen: HashSet<(Option<String>, String)>,
    /// Total operator count
    operators: u32,
    /// Total operand count
    operands: u32,
}

impl HalsteadMetrics {
    /// h1 = distinct operators (η₁)
    pub fn h1(&self) -> u32 {
        self.operators_seen.len() as u32
    }

    /// h2 = distinct operands (η₂)
    pub fn h2(&self) -> u32 {
        self.operands_seen.len() as u32
    }

    /// N1 = total operators
    pub fn n1(&self) -> u32 {
        self.operators
    }

    /// N2 = total operands
    pub fn n2(&self) -> u32 {
        self.operands
    }

    pub fn vocabulary(&self) -> u32 {
        self.h1() + self.h2()
    }

    pub fn length(&self) -> u32 {
        self.n1() + self.n2()
    }

    pub fn volume(&self) -> f64 {
        let vocab = self.vocabulary();
        if vocab == 0 {
            return 0.0;
        }
        self.length() as f64 * (vocab as f64).log2()
    }

    pub fn difficulty(&self) -> f64 {
        // Radon's formula: (h1 * N2) / (2 * h2)
        // where h1 = distinct operators, h2 = distinct operands, N2 = total operands
        let h1 = self.h1();
        let h2 = self.h2();
        let n2 = self.n2();

        if h2 == 0 {
            return 0.0;
        }

        (h1 as f64 * n2 as f64) / (2.0 * h2 as f64)
    }

    pub fn effort(&self) -> f64 {
        self.difficulty() * self.volume()
    }

    fn merge(&mut self, other: &HalsteadMetrics) {
        self.operators_seen
            .extend(other.operators_seen.iter().cloned());
        self.operands_seen
            .extend(other.operands_seen.iter().cloned());
        self.operators += other.operators;
        self.operands += other.operands;
    }

    fn to_pydict<'py>(&self, py: Python<'py>) -> PyResult<pyo3::Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("h1", self.h1())?;
        dict.set_item("h2", self.h2())?;
        dict.set_item("N1", self.n1())?;
        dict.set_item("N2", self.n2())?;
        dict.set_item("vocabulary", self.vocabulary())?;
        dict.set_item("length", self.length())?;
        dict.set_item("volume", self.volume())?;
        dict.set_item("difficulty", self.difficulty())?;
        dict.set_item("effort", self.effort())?;
        Ok(dict)
    }
}

/// Result for a function/method with line info
#[derive(Debug, Clone)]
pub struct FunctionHalstead {
    pub name: String,
    pub start_offset: u32,
    pub end_offset: u32,
    pub metrics: HalsteadMetrics,
}

impl FunctionHalstead {
    fn to_pydict<'py>(
        &self,
        py: Python<'py>,
        line_index: &LineIndex,
    ) -> PyResult<pyo3::Bound<'py, PyDict>> {
        let dict = self.metrics.to_pydict(py)?;

        let lineno = line_index.line_index(TextSize::new(self.start_offset));
        let endline = line_index.line_index(TextSize::new(self.end_offset));
        dict.set_item("lineno", lineno.to_zero_indexed() + 1)?;
        dict.set_item("endline", endline.to_zero_indexed() + 1)?;

        Ok(dict)
    }
}

/// Visitor that collects Halstead metrics
struct HalsteadVisitor<'src> {
    /// Source code (for generating operand repr strings)
    source: &'src str,
    /// Current function context (for tracking unique operands per context)
    context: Option<String>,
    /// Metrics for current scope
    metrics: HalsteadMetrics,
    /// Collected function metrics
    functions: Vec<FunctionHalstead>,
}

impl<'src> HalsteadVisitor<'src> {
    fn new(source: &'src str, context: Option<String>) -> Self {
        Self {
            source,
            context,
            metrics: HalsteadMetrics::default(),
            functions: Vec::new(),
        }
    }

    fn add_operator(&mut self, op_name: &str) {
        self.metrics.operators += 1;
        self.metrics.operators_seen.insert(op_name.to_string());
    }

    fn add_operand(&mut self, operand: &str) {
        self.metrics.operands += 1;
        self.metrics
            .operands_seen
            .insert((self.context.clone(), operand.to_string()));
    }

    /// Get the operator name from a binary operator
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

    /// Get the operator name from a unary operator
    fn unaryop_name(op: &ast::UnaryOp) -> &'static str {
        match op {
            ast::UnaryOp::Invert => "Invert",
            ast::UnaryOp::Not => "Not",
            ast::UnaryOp::UAdd => "UAdd",
            ast::UnaryOp::USub => "USub",
        }
    }

    /// Get the operator name from a boolean operator
    fn boolop_name(op: &ast::BoolOp) -> &'static str {
        match op {
            ast::BoolOp::And => "And",
            ast::BoolOp::Or => "Or",
        }
    }

    /// Get the operator name from a comparison operator
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

    /// Extract operand string from an expression - radon uses simple values
    fn expr_to_operand(expr: &Expr) -> String {
        match expr {
            Expr::Name(n) => n.id.to_string(),
            Expr::NumberLiteral(n) => {
                // Return the numeric value as a string
                match &n.value {
                    ast::Number::Int(i) => i.to_string(),
                    ast::Number::Float(f) => f.to_string(),
                    ast::Number::Complex { real, imag } => format!("{}+{}j", real, imag),
                }
            }
            Expr::StringLiteral(s) => format!("{:?}", s.value.to_str()),
            Expr::BytesLiteral(b) => format!("{:?}", b.value),
            Expr::BooleanLiteral(b) => b.value.to_string(),
            Expr::NoneLiteral(_) => "None".to_string(),
            Expr::EllipsisLiteral(_) => "...".to_string(),
            Expr::Attribute(a) => a.attr.to_string(),
            _ => format!("{:?}", expr),
        }
    }

    /// Get a string representation of an expression (for BoolOp operands)
    /// Radon stores the entire AST node as the operand
    fn expr_repr(&self, expr: &Expr) -> String {
        // Get the source text for this expression
        let start = expr.range().start().to_usize();
        let end = expr.range().end().to_usize();
        if start < self.source.len() && end <= self.source.len() {
            self.source[start..end].to_string()
        } else {
            format!("{:?}", expr)
        }
    }

    /// Visit a function definition
    fn visit_function(&mut self, node: &ast::StmtFunctionDef) {
        // Radon does NOT prefix method names with class name - just use the function name
        let func_name = node.name.to_string();

        let mut func_visitor = HalsteadVisitor::new(self.source, Some(func_name.clone()));

        // Visit the function body
        for stmt in &node.body {
            func_visitor.visit_stmt(stmt);
        }

        // Store function metrics (before merging so we keep per-function metrics separate)
        let func_metrics = func_visitor.metrics.clone();
        self.functions.push(FunctionHalstead {
            name: func_name,
            start_offset: node.range().start().to_u32(),
            end_offset: node.range().end().to_u32(),
            metrics: func_metrics,
        });

        // Merge function metrics into parent for total (radon compatibility)
        // The total includes all code in the file, not just module-level code
        self.metrics.merge(&func_visitor.metrics);
    }

    /// Visit a class definition
    fn visit_class(&mut self, node: &ast::StmtClassDef) {
        // Visit the body, methods will be visited as functions
        for stmt in &node.body {
            self.visit_stmt(stmt);
        }
    }
}

impl<'a, 'src> Visitor<'a> for HalsteadVisitor<'src> {
    fn visit_stmt(&mut self, stmt: &'a Stmt) {
        match stmt {
            Stmt::FunctionDef(node) => {
                self.visit_function(node);
            }
            Stmt::ClassDef(node) => {
                self.visit_class(node);
            }
            // Note: Radon does NOT count Import, ImportFrom, or Assign statements
            // as operators. Only AugAssign is counted (using its underlying op).
            Stmt::AugAssign(node) => {
                // Augmented assignment: 1 operator, 2 operands (target, value)
                self.add_operator(Self::binop_name(&node.op));
                self.add_operand(&Self::expr_to_operand(&node.target));
                self.add_operand(&Self::expr_to_operand(&node.value));
                visitor::walk_stmt(self, stmt);
            }
            _ => {
                visitor::walk_stmt(self, stmt);
            }
        }
    }

    fn visit_expr(&mut self, expr: &'a Expr) {
        match expr {
            Expr::BinOp(node) => {
                // Binary operator: 1 operator, 2 operands
                self.add_operator(Self::binop_name(&node.op));
                self.add_operand(&Self::expr_to_operand(&node.left));
                self.add_operand(&Self::expr_to_operand(&node.right));
                visitor::walk_expr(self, expr);
            }
            Expr::UnaryOp(node) => {
                // Unary operator: 1 operator, 1 operand
                self.add_operator(Self::unaryop_name(&node.op));
                self.add_operand(&Self::expr_to_operand(&node.operand));
                visitor::walk_expr(self, expr);
            }
            Expr::BoolOp(node) => {
                // Boolean operator: 1 operator, N operands
                // Radon stores the entire sub-expressions as operands!
                self.add_operator(Self::boolop_name(&node.op));
                for value in &node.values {
                    self.add_operand(&self.expr_repr(value));
                }
                visitor::walk_expr(self, expr);
            }
            Expr::Compare(node) => {
                // Comparison: N operators (for chained comparisons), N+1 operands
                for op in &node.ops {
                    self.add_operator(Self::cmpop_name(op));
                }
                self.add_operand(&Self::expr_to_operand(&node.left));
                for comp in &node.comparators {
                    self.add_operand(&Self::expr_to_operand(comp));
                }
                visitor::walk_expr(self, expr);
            }
            _ => {
                visitor::walk_expr(self, expr);
            }
        }
    }
}

/// Analyze source code and return Halstead metrics
fn analyze_source(
    source: &str,
) -> Result<(HalsteadMetrics, Vec<FunctionHalstead>, LineIndex), String> {
    let parsed = parse_module(source).map_err(|e| e.to_string())?;
    let line_index = LineIndex::from_source_text(source);

    let mut visitor = HalsteadVisitor::new(source, None);

    for stmt in parsed.suite() {
        visitor.visit_stmt(stmt);
    }

    Ok((visitor.metrics, visitor.functions, line_index))
}

/// Public API for parallel module - returns full analysis results.
pub fn analyze_source_full(
    source: &str,
) -> Result<(Vec<FunctionHalstead>, HalsteadMetrics, LineIndex), String> {
    analyze_source(source).map(|(total, functions, line_index)| (functions, total, line_index))
}

#[pyfunction]
pub fn harvest_halstead_metrics(
    py: Python<'_>,
    entries: Vec<(String, String)>,
) -> PyResult<Vec<(String, Py<PyDict>)>> {
    let mut results = Vec::with_capacity(entries.len());

    for (name, source) in entries {
        let dict = PyDict::new(py);

        match analyze_source(&source) {
            Ok((total_metrics, functions, line_index)) => {
                // Total metrics (no line info for total)
                let total_dict = total_metrics.to_pydict(py)?;
                total_dict.set_item("lineno", py.None())?;
                total_dict.set_item("endline", py.None())?;
                dict.set_item("total", total_dict)?;

                // Function metrics
                let funcs_dict = PyDict::new(py);
                for func in &functions {
                    funcs_dict.set_item(&func.name, func.to_pydict(py, &line_index)?)?;
                }
                dict.set_item("functions", funcs_dict)?;
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
    module.add_function(wrap_pyfunction!(harvest_halstead_metrics, module)?)?;
    Ok(())
}
