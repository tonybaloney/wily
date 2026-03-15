//! Cyclomatic complexity calculation using Ruff's AST.
//!
//! This module calculates cyclomatic complexity metrics compatible with Radon:
//! - Each function/method gets a complexity score starting at 1
//! - Decision points (if, for, while, except, and, or, etc.) add to complexity

use ruff_python_ast::{
    self as ast,
    visitor::{self, Visitor},
    Expr, ModModule, Pattern, Stmt,
};
use ruff_text_size::Ranged;

/// Result for a single function/method (storing byte offsets)
#[derive(Debug, Clone)]
pub struct FunctionComplexity {
    pub name: String,
    pub start_offset: u32, // byte offset
    pub end_offset: u32,   // byte offset
    pub is_method: bool,
    pub classname: Option<String>,
    pub complexity: u32,
}

impl FunctionComplexity {
    pub fn fullname(&self) -> String {
        match &self.classname {
            Some(cls) => format!("{}.{}", cls, self.name),
            None => self.name.clone(),
        }
    }
}

/// Result for a class (storing byte offsets)
#[derive(Debug, Clone)]
pub struct ClassComplexity {
    pub name: String,
    pub start_offset: u32, // byte offset
    pub end_offset: u32,   // byte offset
    pub methods: Vec<FunctionComplexity>,
    pub real_complexity: u32,
}

impl ClassComplexity {
    /// Average complexity of methods + 1 (if multiple methods)
    pub fn complexity(&self) -> u32 {
        if self.methods.is_empty() {
            self.real_complexity
        } else {
            let methods_count = self.methods.len() as u32;
            let avg = self.real_complexity / methods_count;
            avg + if methods_count > 1 { 1 } else { 0 }
        }
    }
}

/// Visitor that calculates cyclomatic complexity
struct ComplexityVisitor {
    /// Current complexity count
    complexity: u32,
    /// Whether we're visiting as a method
    is_method: bool,
    /// Parent class name if visiting a method
    classname: Option<String>,
    /// Whether to count assert statements
    no_assert: bool,
    /// Collected functions
    functions: Vec<FunctionComplexity>,
    /// Collected classes
    classes: Vec<ClassComplexity>,
}

impl ComplexityVisitor {
    fn new(is_method: bool, classname: Option<String>, no_assert: bool) -> Self {
        Self {
            complexity: 1, // Start at 1 per radon
            is_method,
            classname,
            no_assert,
            functions: Vec::new(),
            classes: Vec::new(),
        }
    }

    /// Visit a function/method definition
    fn visit_function(&mut self, node: &ast::StmtFunctionDef) {
        let mut body_complexity = 1u32;
        let mut closures = Vec::new();

        // Visit each statement in the function body
        for stmt in &node.body {
            let mut visitor = ComplexityVisitor::new(false, None, self.no_assert);
            visitor.complexity = 0; // Start at 0 for body
            visitor.visit_stmt(stmt);

            // Collect closures (nested functions)
            closures.extend(visitor.functions);

            // Add body complexity (not closure complexity per radon #68)
            body_complexity += visitor.complexity;
        }

        let func = FunctionComplexity {
            name: node.name.to_string(),
            start_offset: node.range().start().to_u32(),
            end_offset: node.range().end().to_u32(),
            is_method: self.is_method,
            classname: self.classname.clone(),
            complexity: body_complexity,
        };

        self.functions.push(func);
    }

    /// Visit a class definition
    fn visit_class(&mut self, node: &ast::StmtClassDef) {
        let mut methods = Vec::new();
        let mut body_complexity = 1u32;
        let mut max_end_offset = node.range().end().to_u32();
        let classname = node.name.to_string();

        // Visit each statement in the class body
        for stmt in &node.body {
            let mut visitor = ComplexityVisitor::new(true, Some(classname.clone()), self.no_assert);
            visitor.complexity = 0;
            visitor.visit_stmt(stmt);

            // Calculate complexity contribution before moving functions
            let funcs_complexity: u32 = visitor.functions.iter().map(|f| f.complexity).sum();
            let funcs_count = visitor.functions.len() as u32;

            // Update max end offset before moving
            for m in &visitor.functions {
                if m.end_offset > max_end_offset {
                    max_end_offset = m.end_offset;
                }
            }

            // Now move the functions
            methods.extend(visitor.functions);

            body_complexity += visitor.complexity + funcs_complexity - funcs_count + funcs_count;
        }

        let cls = ClassComplexity {
            name: classname,
            start_offset: node.range().start().to_u32(),
            end_offset: max_end_offset,
            methods,
            real_complexity: body_complexity,
        };

        self.classes.push(cls);
    }

    /// Check if a match case uses wildcard pattern (_)
    fn is_wildcard_pattern(pattern: &Pattern) -> bool {
        matches!(
            pattern,
            Pattern::MatchAs(ast::PatternMatchAs { pattern: None, .. })
        )
    }
}

impl<'a> Visitor<'a> for ComplexityVisitor {
    fn visit_stmt(&mut self, stmt: &'a Stmt) {
        match stmt {
            Stmt::FunctionDef(node) => {
                self.visit_function(node);
            }
            Stmt::ClassDef(node) => {
                self.visit_class(node);
            }
            Stmt::If(node) => {
                // if statement adds 1, plus 1 for each elif clause
                // elif_else_clauses contains both elif (has test) and else (no test)
                let elif_count = node
                    .elif_else_clauses
                    .iter()
                    .filter(|clause| clause.test.is_some())
                    .count() as u32;
                self.complexity += 1 + elif_count;
                visitor::walk_stmt(self, stmt);
            }
            Stmt::For(node) => {
                // for adds 1, plus 1 if there's an else
                self.complexity += 1 + if node.orelse.is_empty() { 0 } else { 1 };
                visitor::walk_stmt(self, stmt);
            }
            Stmt::While(node) => {
                // while adds 1, plus 1 if there's an else
                self.complexity += 1 + if node.orelse.is_empty() { 0 } else { 1 };
                visitor::walk_stmt(self, stmt);
            }
            Stmt::Try(node) => {
                // try adds number of except handlers + 1 if there's an else
                self.complexity +=
                    node.handlers.len() as u32 + if node.orelse.is_empty() { 0 } else { 1 };
                visitor::walk_stmt(self, stmt);
            }
            Stmt::Match(node) => {
                // Match adds number of cases, minus 1 if there's a wildcard (_)
                let has_wildcard = node
                    .cases
                    .iter()
                    .any(|case| Self::is_wildcard_pattern(&case.pattern));
                let case_count = node.cases.len() as u32;
                self.complexity += if has_wildcard {
                    case_count.saturating_sub(1)
                } else {
                    case_count
                };
                visitor::walk_stmt(self, stmt);
            }
            Stmt::Assert(_) => {
                // assert adds 1 only if no_assert is false
                if !self.no_assert {
                    self.complexity += 1;
                }
                visitor::walk_stmt(self, stmt);
            }
            _ => {
                visitor::walk_stmt(self, stmt);
            }
        }
    }

    fn visit_expr(&mut self, expr: &'a Expr) {
        match expr {
            Expr::If(_) => {
                // Ternary expression adds 1
                self.complexity += 1;
                visitor::walk_expr(self, expr);
            }
            Expr::BoolOp(node) => {
                // and/or adds (number of values - 1)
                self.complexity += (node.values.len() as u32).saturating_sub(1);
                visitor::walk_expr(self, expr);
            }
            Expr::ListComp(node) => {
                // List comprehension: 1 per generator + number of ifs
                for gen in &node.generators {
                    self.complexity += 1 + gen.ifs.len() as u32;
                }
                visitor::walk_expr(self, expr);
            }
            Expr::SetComp(node) => {
                for gen in &node.generators {
                    self.complexity += 1 + gen.ifs.len() as u32;
                }
                visitor::walk_expr(self, expr);
            }
            Expr::DictComp(node) => {
                for gen in &node.generators {
                    self.complexity += 1 + gen.ifs.len() as u32;
                }
                visitor::walk_expr(self, expr);
            }
            Expr::Generator(node) => {
                for gen in &node.generators {
                    self.complexity += 1 + gen.ifs.len() as u32;
                }
                visitor::walk_expr(self, expr);
            }
            _ => {
                visitor::walk_expr(self, expr);
            }
        }
    }

    fn visit_comprehension(&mut self, _comprehension: &'a ast::Comprehension) {
        // Already handled in ListComp/SetComp/DictComp/Generator
    }
}

pub fn analyze(
    parsed: &ruff_python_parser::Parsed<ModModule>,
) -> (Vec<FunctionComplexity>, Vec<ClassComplexity>) {
    let mut visitor = ComplexityVisitor::new(false, None, true); // no_assert=true by default

    for stmt in parsed.suite() {
        visitor.visit_stmt(stmt);
    }

    // Radon also includes class methods in the functions list (not just classes)
    // So we need to flatten the methods out
    let mut all_functions = visitor.functions;
    for class in &visitor.classes {
        for method in &class.methods {
            all_functions.push(method.clone());
        }
    }

    (all_functions, visitor.classes)
}
