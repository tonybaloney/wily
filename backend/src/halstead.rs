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

use compact_str::CompactString;
use ruff_python_ast::{
    self as ast, Expr, ModModule, Stmt, visitor::{self, Visitor}
};
use ruff_text_size::Ranged;
use std::collections::HashSet;

/// Halstead metrics for a code block
#[derive(Debug, Clone, Default)]
pub struct HalsteadMetrics {
    /// Set of unique operators seen (stored as &'static str for efficiency)
    operators_seen: HashSet<&'static str>,
    /// Set of unique operands seen (context index, operand repr)
    /// Using CompactString to inline short strings (up to 24 bytes on 64-bit)
    operands_seen: HashSet<(u32, CompactString)>,
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
        self.operators_seen.extend(other.operators_seen.iter());
        self.operands_seen
            .extend(other.operands_seen.iter().cloned());
        self.operators += other.operators;
        self.operands += other.operands;
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

/// Visitor that collects Halstead metrics
struct HalsteadVisitor<'src> {
    /// Source code (for generating operand repr strings)
    source: &'src str,
    /// Current function context index (0 = module level, 1+ = function index)
    context_idx: u32,
    /// Metrics for current scope
    metrics: HalsteadMetrics,
    /// Collected function metrics
    functions: Vec<FunctionHalstead>,
    /// Next context index to assign
    next_context_idx: u32,
}

impl<'src> HalsteadVisitor<'src> {
    fn new(source: &'src str, context_idx: u32) -> Self {
        Self {
            source,
            context_idx,
            metrics: HalsteadMetrics::default(),
            functions: Vec::new(),
            next_context_idx: context_idx + 1,
        }
    }

    #[inline]
    fn add_operator(&mut self, op_name: &'static str) {
        self.metrics.operators += 1;
        self.metrics.operators_seen.insert(op_name);
    }

    #[inline]
    fn add_operand(&mut self, operand: CompactString) {
        self.metrics.operands += 1;
        self.metrics.operands_seen.insert((self.context_idx, operand));
    }

    /// Get the operator name from a binary operator
    fn binop_name(op: &ast::Operator) -> &'static str {
        op.dunder()
    }

    /// Get the operator name from a unary operator
    fn unaryop_name(op: &ast::UnaryOp) -> &'static str {
        op.as_str()
    }

    /// Get the operator name from a boolean operator
    fn boolop_name(op: &ast::BoolOp) -> &'static str {
        op.as_str()
    }

    /// Get the operator name from a comparison operator
    fn cmpop_name(op: &ast::CmpOp) -> &'static str {
        op.as_str()
    }

    /// Extract operand string from an expression - radon uses simple values
    #[inline]
    fn expr_to_operand(expr: &Expr) -> CompactString {
        match expr {
            Expr::Name(n) => CompactString::new(&n.id),
            Expr::NumberLiteral(n) => {
                // Return the numeric value as a string
                match &n.value {
                    ast::Number::Int(i) => CompactString::new(i.to_string()),
                    ast::Number::Float(f) => CompactString::new(f.to_string()),
                    ast::Number::Complex { real, imag } => CompactString::new(format!("{}+{}j", real, imag)),
                }
            }
            Expr::StringLiteral(s) => CompactString::new(format!("{:?}", s.value.to_str())),
            Expr::BytesLiteral(b) => CompactString::new(format!("{:?}", b.value)),
            Expr::BooleanLiteral(b) => CompactString::const_new(if b.value { "True" } else { "False" }),
            Expr::NoneLiteral(_) => CompactString::const_new("None"),
            Expr::EllipsisLiteral(_) => CompactString::const_new("..."),
            Expr::Attribute(a) => CompactString::new(&a.attr),
            _ => CompactString::new(format!("{:?}", expr)),
        }
    }

    /// Get a string representation of an expression (for BoolOp operands)
    /// Radon stores the entire AST node as the operand
    #[inline]
    fn expr_repr(&self, expr: &Expr) -> CompactString {
        // Get the source text for this expression
        let start = expr.range().start().to_usize();
        let end = expr.range().end().to_usize();
        if start < self.source.len() && end <= self.source.len() {
            CompactString::new(&self.source[start..end])
        } else {
            CompactString::new(format!("{:?}", expr))
        }
    }

    /// Visit a function definition
    fn visit_function(&mut self, node: &ast::StmtFunctionDef) {
        // Radon does NOT prefix method names with class name - just use the function name
        let func_name = node.name.to_string();

        // Assign a unique context index for this function
        let func_context_idx = self.next_context_idx;
        self.next_context_idx += 1;

        let mut func_visitor = HalsteadVisitor::new(self.source, func_context_idx);
        func_visitor.next_context_idx = self.next_context_idx;

        // Visit the function body
        for stmt in &node.body {
            func_visitor.visit_stmt(stmt);
        }

        // Update our next_context_idx from nested functions
        self.next_context_idx = func_visitor.next_context_idx;

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
                self.add_operand(Self::expr_to_operand(&node.target));
                self.add_operand(Self::expr_to_operand(&node.value));
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
                self.add_operand(Self::expr_to_operand(&node.left));
                self.add_operand(Self::expr_to_operand(&node.right));
                visitor::walk_expr(self, expr);
            }
            Expr::UnaryOp(node) => {
                // Unary operator: 1 operator, 1 operand
                self.add_operator(Self::unaryop_name(&node.op));
                self.add_operand(Self::expr_to_operand(&node.operand));
                visitor::walk_expr(self, expr);
            }
            Expr::BoolOp(node) => {
                // Boolean operator: 1 operator, N operands
                // Radon stores the entire sub-expressions as operands!
                self.add_operator(Self::boolop_name(&node.op));
                for value in &node.values {
                    self.add_operand(self.expr_repr(value));
                }
                visitor::walk_expr(self, expr);
            }
            Expr::Compare(node) => {
                // Comparison: N operators (for chained comparisons), N+1 operands
                for op in &node.ops {
                    self.add_operator(Self::cmpop_name(op));
                }
                self.add_operand(Self::expr_to_operand(&node.left));
                for comp in &node.comparators {
                    self.add_operand(Self::expr_to_operand(comp));
                }
                visitor::walk_expr(self, expr);
            }
            _ => {
                visitor::walk_expr(self, expr);
            }
        }
    }
}

/// Public API for parallel module - returns full analysis results.
pub fn analyze(
    source: &str,
    parsed: &ruff_python_parser::Parsed<ModModule>
) -> (HalsteadMetrics, Vec<FunctionHalstead>) {
    let mut visitor = HalsteadVisitor::new(source, 0);

    for stmt in parsed.suite() {
        visitor.visit_stmt(stmt);
    }

    (visitor.metrics, visitor.functions)
}
