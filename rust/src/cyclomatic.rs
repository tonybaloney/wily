//! Cyclomatic complexity calculation using Ruff's AST.
//!
//! This module calculates cyclomatic complexity metrics compatible with Radon:
//! - Each function/method gets a complexity score starting at 1
//! - Decision points (if, for, while, except, and, or, etc.) add to complexity

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};
use ruff_python_ast::{
    self as ast, Expr, Pattern, Stmt,
    visitor::{self, Visitor},
};
use ruff_python_parser::parse_module;
use ruff_source_file::LineIndex;
use ruff_text_size::{Ranged, TextSize};

/// Result for a single function/method (storing byte offsets)
#[derive(Debug, Clone)]
struct FunctionComplexity {
    name: String,
    start_offset: u32,  // byte offset
    end_offset: u32,    // byte offset
    is_method: bool,
    classname: Option<String>,
    complexity: u32,
    closures: Vec<FunctionComplexity>,
}

impl FunctionComplexity {
    fn fullname(&self) -> String {
        match &self.classname {
            Some(cls) => format!("{}.{}", cls, self.name),
            None => self.name.clone(),
        }
    }

    fn to_pydict<'py>(&self, py: Python<'py>, line_index: &LineIndex) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("name", &self.name)?;
        
        let lineno = line_index.line_index(TextSize::new(self.start_offset));
        let endline = line_index.line_index(TextSize::new(self.end_offset));
        dict.set_item("lineno", lineno.to_zero_indexed() + 1)?;  // 1-indexed
        dict.set_item("col_offset", 0u32)?;  // TODO: get actual column
        dict.set_item("endline", endline.to_zero_indexed() + 1)?;  // 1-indexed
        dict.set_item("is_method", self.is_method)?;
        dict.set_item("classname", self.classname.as_deref())?;
        dict.set_item("complexity", self.complexity)?;
        dict.set_item("fullname", self.fullname())?;
        
        let closures_list = PyList::empty(py);
        for closure in &self.closures {
            closures_list.append(closure.to_pydict(py, line_index)?)?;
        }
        dict.set_item("closures", closures_list)?;
        
        Ok(dict)
    }
}

/// Result for a class (storing byte offsets)
#[derive(Debug, Clone)]
struct ClassComplexity {
    name: String,
    start_offset: u32,  // byte offset
    end_offset: u32,    // byte offset
    methods: Vec<FunctionComplexity>,
    inner_classes: Vec<ClassComplexity>,
    real_complexity: u32,
}

impl ClassComplexity {
    /// Average complexity of methods + 1 (if multiple methods)
    fn complexity(&self) -> u32 {
        if self.methods.is_empty() {
            self.real_complexity
        } else {
            let methods_count = self.methods.len() as u32;
            let avg = self.real_complexity / methods_count;
            avg + if methods_count > 1 { 1 } else { 0 }
        }
    }

    fn to_pydict<'py>(&self, py: Python<'py>, line_index: &LineIndex) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("name", &self.name)?;
        
        let lineno = line_index.line_index(TextSize::new(self.start_offset));
        let endline = line_index.line_index(TextSize::new(self.end_offset));
        dict.set_item("lineno", lineno.to_zero_indexed() + 1)?;  // 1-indexed
        dict.set_item("col_offset", 0u32)?;  // TODO
        dict.set_item("endline", endline.to_zero_indexed() + 1)?;  // 1-indexed
        dict.set_item("complexity", self.complexity())?;
        dict.set_item("real_complexity", self.real_complexity)?;
        dict.set_item("fullname", &self.name)?;
        
        let methods_list = PyList::empty(py);
        for method in &self.methods {
            methods_list.append(method.to_pydict(py, line_index)?)?;
        }
        dict.set_item("methods", methods_list)?;
        
        let inner_list = PyList::empty(py);
        for inner in &self.inner_classes {
            inner_list.append(inner.to_pydict(py, line_index)?)?;
        }
        dict.set_item("inner_classes", inner_list)?;
        
        Ok(dict)
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
            closures,
        };

        self.functions.push(func);
    }

    /// Visit a class definition
    fn visit_class(&mut self, node: &ast::StmtClassDef) {
        let mut methods = Vec::new();
        let mut body_complexity = 1u32;
        let mut inner_classes = Vec::new();
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
            inner_classes.extend(visitor.classes);

            body_complexity += visitor.complexity + funcs_complexity - funcs_count + funcs_count;
        }

        let cls = ClassComplexity {
            name: classname,
            start_offset: node.range().start().to_u32(),
            end_offset: max_end_offset,
            methods,
            inner_classes,
            real_complexity: body_complexity,
        };

        self.classes.push(cls);
    }

    /// Check if a match case uses wildcard pattern (_)
    fn is_wildcard_pattern(pattern: &Pattern) -> bool {
        match pattern {
            Pattern::MatchAs(ast::PatternMatchAs { pattern: None, .. }) => true,
            _ => false,
        }
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
                let elif_count = node.elif_else_clauses.iter()
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
                self.complexity += node.handlers.len() as u32 + if node.orelse.is_empty() { 0 } else { 1 };
                visitor::walk_stmt(self, stmt);
            }
            Stmt::Match(node) => {
                // Match adds number of cases, minus 1 if there's a wildcard (_)
                let has_wildcard = node.cases.iter().any(|case| Self::is_wildcard_pattern(&case.pattern));
                let case_count = node.cases.len() as u32;
                self.complexity += if has_wildcard { case_count.saturating_sub(1) } else { case_count };
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

/// Analyze source code and return cyclomatic complexity results
fn analyze_source(source: &str) -> Result<(Vec<FunctionComplexity>, Vec<ClassComplexity>, LineIndex), String> {
    let parsed = parse_module(source).map_err(|e| e.to_string())?;
    let line_index = LineIndex::from_source_text(source);
    
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
    
    Ok((all_functions, visitor.classes, line_index))
}

#[pyfunction]
pub fn harvest_cyclomatic_metrics(
    py: Python<'_>,
    entries: Vec<(String, String)>,
) -> PyResult<Vec<(String, Py<PyDict>)>> {
    let mut results = Vec::with_capacity(entries.len());

    for (name, source) in entries {
        let dict = PyDict::new(py);
        
        match analyze_source(&source) {
            Ok((functions, classes, line_index)) => {
                let funcs_list = PyList::empty(py);
                for func in &functions {
                    funcs_list.append(func.to_pydict(py, &line_index)?)?;
                }
                dict.set_item("functions", funcs_list)?;
                
                let classes_list = PyList::empty(py);
                for cls in &classes {
                    classes_list.append(cls.to_pydict(py, &line_index)?)?;
                }
                dict.set_item("classes", classes_list)?;
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
    module.add_function(wrap_pyfunction!(harvest_cyclomatic_metrics, module)?)?;
    Ok(())
}
