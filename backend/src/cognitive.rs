//! Cognitive complexity calculation using Ruff's AST.
//!
//! Implements the cognitive complexity metric as defined by G. Ann Campbell
//! in "Cognitive Complexity: A new way of measuring understandability"
//! (SonarSource, 2017).
//!
//! Unlike cyclomatic complexity which counts decision points equally,
//! cognitive complexity penalizes nesting depth and distinguishes between
//! constructs that are easy vs hard for humans to understand.
//!
//! Reference implementation: https://github.com/rohaquinlop/complexipy (MIT license)

use ruff_python_ast::{self as ast, Expr, ModModule, Stmt};
use ruff_text_size::Ranged;

/// Result for a single function/method (storing byte offsets)
#[derive(Debug, Clone)]
pub struct FunctionCognitiveComplexity {
    pub name: String,
    pub start_offset: u32,
    pub end_offset: u32,
    pub is_method: bool,
    pub classname: Option<String>,
    pub complexity: u64,
}

impl FunctionCognitiveComplexity {
    pub fn fullname(&self) -> String {
        match &self.classname {
            Some(cls) => format!("{}.{}", cls, self.name),
            None => self.name.clone(),
        }
    }
}

/// Analyze a parsed module and return per-function cognitive complexity.
pub fn analyze(parsed: &ruff_python_parser::Parsed<ModModule>) -> Vec<FunctionCognitiveComplexity> {
    let mut functions = Vec::new();

    for stmt in parsed.suite() {
        match stmt {
            Stmt::FunctionDef(f) => {
                let complexity = statement_cognitive_complexity(stmt, 0);
                functions.push(FunctionCognitiveComplexity {
                    name: f.name.to_string(),
                    start_offset: f.range().start().to_u32(),
                    end_offset: f.range().end().to_u32(),
                    is_method: false,
                    classname: None,
                    complexity,
                });
            }
            Stmt::ClassDef(c) => {
                for node in c.body.iter() {
                    if let Stmt::FunctionDef(f) = node {
                        let complexity = statement_cognitive_complexity(node, 0);
                        functions.push(FunctionCognitiveComplexity {
                            name: f.name.to_string(),
                            start_offset: f.range().start().to_u32(),
                            end_offset: f.range().end().to_u32(),
                            is_method: true,
                            classname: Some(c.name.to_string()),
                            complexity,
                        });
                    }
                }
            }
            _ => {}
        }
    }

    functions
}

/// Calculate the cognitive complexity of a single statement, recursively.
///
/// The algorithm follows G. Ann Campbell's paper:
/// - **Increments (+1):** for, while, if, except, with, break/continue (to label),
///   sequences of same boolean operators, ternary, nested functions, comprehensions
/// - **Nesting penalty:** each of the above (except boolean ops and else/elif)
///   also adds the current nesting level
/// - **Nesting increases:** if, elif, else, for, while, try, with,
///   nested function defs, and comprehensions increase nesting for their bodies
fn statement_cognitive_complexity(statement: &Stmt, nesting_level: u64) -> u64 {
    let mut complexity: u64 = 0;

    // Handle decorator pattern: a function with exactly one inner function + return
    // is treated as a decorator, so we skip to the inner function.
    if is_decorator(statement) {
        if let Stmt::FunctionDef(f) = statement {
            return statement_cognitive_complexity(&f.body[0], nesting_level);
        }
    }

    match statement {
        Stmt::FunctionDef(f) => {
            for node in f.body.iter() {
                match node {
                    // Nested function definitions increase nesting
                    Stmt::FunctionDef(..) => {
                        complexity += statement_cognitive_complexity(node, nesting_level + 1);
                    }
                    _ => {
                        complexity += statement_cognitive_complexity(node, nesting_level);
                    }
                }
            }
        }
        Stmt::ClassDef(c) => {
            for node in c.body.iter() {
                if let Stmt::FunctionDef(..) = node {
                    complexity += statement_cognitive_complexity(node, nesting_level);
                }
            }
        }
        Stmt::If(i) => {
            // if: +1 + nesting_level, plus bool ops in the test
            complexity += 1 + nesting_level + count_bool_ops(&i.test, nesting_level);
            for node in i.body.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
            // elif/else clauses: +1 each (no nesting penalty for the clause itself)
            for clause in i.elif_else_clauses.iter() {
                let mut clause_complexity = 1u64;
                if let Some(test) = &clause.test {
                    clause_complexity += count_bool_ops(test, nesting_level);
                }
                complexity += clause_complexity;
                for node in clause.body.iter() {
                    complexity += statement_cognitive_complexity(node, nesting_level + 1);
                }
            }
        }
        Stmt::For(f) => {
            // for: +1 + nesting_level
            complexity += 1 + nesting_level;
            for node in f.body.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
            for node in f.orelse.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
        }
        Stmt::While(w) => {
            // while: +1 + nesting_level + bool ops in condition
            complexity += 1 + nesting_level + count_bool_ops(&w.test, nesting_level);
            for node in w.body.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
            for node in w.orelse.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
        }
        Stmt::Try(t) => {
            // try body runs at increased nesting
            for node in t.body.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
            // Each except handler: +1
            for handler in t.handlers.iter() {
                complexity += 1;
                let handler = handler.as_except_handler().unwrap();
                for node in handler.body.iter() {
                    complexity += statement_cognitive_complexity(node, nesting_level + 1);
                }
            }
            for node in t.orelse.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
            for node in t.finalbody.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
        }
        Stmt::Match(m) => {
            for case in m.cases.iter() {
                for node in case.body.iter() {
                    complexity += statement_cognitive_complexity(node, nesting_level + 1);
                }
            }
        }
        Stmt::With(w) => {
            // Count bool ops in context expressions
            for item in w.items.iter() {
                complexity += count_bool_ops(&item.context_expr, nesting_level);
            }
            for node in w.body.iter() {
                complexity += statement_cognitive_complexity(node, nesting_level + 1);
            }
        }
        Stmt::Assign(a) => {
            complexity += count_bool_ops(&a.value, nesting_level);
        }
        Stmt::AnnAssign(a) => {
            if let Some(value) = &a.value {
                complexity += count_bool_ops(value, nesting_level);
            }
        }
        Stmt::AugAssign(a) => {
            complexity += count_bool_ops(&a.value, nesting_level);
        }
        Stmt::Return(r) => {
            if let Some(value) = &r.value {
                complexity += count_bool_ops(value, nesting_level);
            }
        }
        Stmt::Raise(r) => {
            if let Some(exc) = &r.exc {
                complexity += count_bool_ops(exc, nesting_level);
            }
            if let Some(cause) = &r.cause {
                complexity += count_bool_ops(cause, nesting_level);
            }
        }
        Stmt::Assert(a) => {
            complexity += count_bool_ops(&a.test, nesting_level);
            if let Some(msg) = &a.msg {
                complexity += count_bool_ops(msg, nesting_level);
            }
        }
        _ => {}
    }

    complexity
}

/// Check if a function looks like a decorator (single inner function + return).
fn is_decorator(statement: &Stmt) -> bool {
    if let Stmt::FunctionDef(f) = statement {
        f.body.len() == 2
            && matches!(f.body[0], Stmt::FunctionDef(..))
            && matches!(f.body[1], Stmt::Return(..))
    } else {
        false
    }
}

/// Count the cognitive complexity contribution of boolean operators and
/// nested expressions within an expression.
///
/// Boolean operators (and/or) add +1 for each *sequence* of the same operator,
/// and +1 when the operator type changes (mixed and/or).
fn count_bool_ops(expr: &Expr, nesting_level: u64) -> u64 {
    let mut complexity: u64 = 0;

    match expr {
        Expr::BoolOp(b) => {
            // A sequence of boolean ops: +1 for the sequence
            complexity += 1;
            // Check children for different boolean op types
            for value in b.values.iter() {
                complexity += count_different_child_types(value, expr);
            }
        }
        Expr::UnaryOp(u) => {
            complexity += count_different_child_types(&u.operand, expr);
        }
        Expr::Compare(c) => {
            complexity += count_bool_ops(&c.left, nesting_level);
            for comparator in c.comparators.iter() {
                complexity += count_bool_ops(comparator, nesting_level);
            }
        }
        Expr::If(i) => {
            // Ternary expression: +1 + nesting
            complexity += 1 + nesting_level;
            complexity += count_bool_ops(&i.test, nesting_level);
            complexity += count_bool_ops(&i.body, nesting_level);
            complexity += count_bool_ops(&i.orelse, nesting_level);
        }
        Expr::Call(c) => {
            for arg in c.arguments.args.iter() {
                complexity += count_bool_ops(arg, nesting_level);
            }
        }
        Expr::Tuple(t) => {
            for element in t.elts.iter() {
                complexity += count_bool_ops(element, nesting_level);
            }
        }
        Expr::List(l) => {
            for element in l.elts.iter() {
                complexity += count_bool_ops(element, nesting_level);
            }
        }
        Expr::Set(s) => {
            for element in s.elts.iter() {
                complexity += count_bool_ops(element, nesting_level);
            }
        }
        Expr::Dict(d) => {
            for value in d.iter_values() {
                complexity += count_bool_ops(value, nesting_level);
            }
        }
        Expr::FString(f) => {
            for element in f.value.elements() {
                if let Some(inter) = element.as_interpolation() {
                    complexity += count_bool_ops(&inter.expression, nesting_level);
                }
            }
        }
        Expr::ListComp(l) => {
            complexity += count_comprehension_complexity(&l.generators, &l.elt, nesting_level);
        }
        Expr::SetComp(s) => {
            complexity += count_comprehension_complexity(&s.generators, &s.elt, nesting_level);
        }
        Expr::Generator(g) => {
            complexity += count_comprehension_complexity(&g.generators, &g.elt, nesting_level);
        }
        Expr::DictComp(d) => {
            complexity += count_comprehension_complexity(&d.generators, &d.key, nesting_level);
            complexity += count_bool_ops(&d.value, nesting_level + 1);
        }
        _ => {}
    }

    complexity
}

/// Score a comprehension expression (list/set/generator/dict).
///
/// Rules:
/// - The comprehension itself: +1 + nesting_level
/// - Each additional `for` clause beyond the first: +1
/// - Each `if` filter: +1, plus any boolean-operator complexity
/// - The element expression and iterators are recursed at nesting_level + 1
fn count_comprehension_complexity(
    generators: &[ast::Comprehension],
    elt: &Expr,
    nesting_level: u64,
) -> u64 {
    let mut complexity: u64 = 1 + nesting_level;

    for (i, clause) in generators.iter().enumerate() {
        if i > 0 {
            complexity += 1;
        }
        for if_expr in clause.ifs.iter() {
            complexity += 1 + count_bool_ops(if_expr, nesting_level + 1);
        }
        complexity += count_bool_ops(&clause.iter, nesting_level + 1);
    }

    complexity += count_bool_ops(elt, nesting_level + 1);

    complexity
}

/// Count complexity from child expressions that differ in boolean operator type
/// from their parent. E.g., `a and b or c` has mixed operators.
fn count_different_child_types(expr: &Expr, parent: &Expr) -> u64 {
    let mut complexity: u64 = 0;

    match expr {
        Expr::BoolOp(b) => match parent {
            Expr::BoolOp(p) => {
                if b.op != p.op {
                    complexity += 1;
                }
                for value in b.values.iter() {
                    complexity += count_different_child_types(value, expr);
                }
            }
            Expr::UnaryOp(p) => {
                complexity = 1 + count_different_child_types(&p.operand, expr);
            }
            _ => {}
        },
        Expr::UnaryOp(_) => match parent {
            Expr::BoolOp(p) => {
                for value in p.values.iter() {
                    complexity += count_different_child_types(value, expr);
                }
            }
            Expr::UnaryOp(p) => {
                complexity = count_different_child_types(&p.operand, expr);
            }
            _ => {}
        },
        _ => {}
    }

    complexity
}

#[cfg(test)]
mod tests {
    use super::*;
    use ruff_python_parser::parse_module;

    fn analyze_code(code: &str) -> Vec<FunctionCognitiveComplexity> {
        let parsed = parse_module(code).unwrap();
        analyze(&parsed)
    }

    fn total_complexity(code: &str) -> u64 {
        analyze_code(code).iter().map(|f| f.complexity).sum()
    }

    #[test]
    fn test_simple_function() {
        let code = "def foo():\n    pass\n";
        assert_eq!(total_complexity(code), 0);
    }

    #[test]
    fn test_single_if() {
        let code = "def foo(x):\n    if x:\n        pass\n";
        // if: +1 (no nesting since it's at function body level = 0)
        assert_eq!(total_complexity(code), 1);
    }

    #[test]
    fn test_nested_if() {
        let code = "def foo(x, y):\n    if x:\n        if y:\n            pass\n";
        // outer if: +1 (nesting=0), inner if: +1 + 1(nesting) = 2
        assert_eq!(total_complexity(code), 3);
    }

    #[test]
    fn test_if_elif_else() {
        let code = "def foo(x):\n    if x:\n        pass\n    elif not x:\n        pass\n    else:\n        pass\n";
        // if: +1, elif: +1, else: +1
        assert_eq!(total_complexity(code), 3);
    }

    #[test]
    fn test_for_loop() {
        let code = "def foo(items):\n    for i in items:\n        pass\n";
        // for: +1
        assert_eq!(total_complexity(code), 1);
    }

    #[test]
    fn test_nested_for_if() {
        let code = "def foo(items):\n    for i in items:\n        if i:\n            pass\n";
        // for: +1 (nesting=0), if: +1 + 1(nesting) = 2
        assert_eq!(total_complexity(code), 3);
    }

    #[test]
    fn test_boolean_ops() {
        let code = "def foo(a, b, c):\n    if a and b and c:\n        pass\n";
        // if: +1, `and` sequence: +1
        assert_eq!(total_complexity(code), 2);
    }

    #[test]
    fn test_mixed_boolean_ops() {
        let code = "def foo(a, b, c):\n    if a and b or c:\n        pass\n";
        // if: +1, first bool op: +1, change from and->or: +1
        assert_eq!(total_complexity(code), 3);
    }

    #[test]
    fn test_try_except() {
        let code = "def foo():\n    try:\n        pass\n    except ValueError:\n        pass\n";
        // except: +1
        assert_eq!(total_complexity(code), 1);
    }

    #[test]
    fn test_while_loop() {
        let code = "def foo(x):\n    while x:\n        x -= 1\n";
        // while: +1
        assert_eq!(total_complexity(code), 1);
    }

    #[test]
    fn test_class_method() {
        let code = "class Foo:\n    def bar(self, x):\n        if x:\n            pass\n";
        let results = analyze_code(code);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].name, "bar");
        assert!(results[0].is_method);
        assert_eq!(results[0].classname.as_deref(), Some("Foo"));
        assert_eq!(results[0].complexity, 1);
    }
}
