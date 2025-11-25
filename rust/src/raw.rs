use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};
use ruff_python_parser::lexer::lex;
use ruff_python_parser::{lexer::Lexer, Mode, TokenKind};

#[derive(Debug, Default, Clone, Copy)]
struct RawCounts {
    loc: u32,
    sloc: u32,
    comments: u32,
    blank: u32,
}

impl RawCounts {
    fn to_pydict<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("loc", self.loc)?;
        dict.set_item("sloc", self.sloc)?;
        dict.set_item("comments", self.comments)?;
        dict.set_item("blank", self.blank)?;
        // Placeholders to maintain compatibility with the existing metric layout.
        dict.set_item("lloc", 0u32)?;
        dict.set_item("multi", 0u32)?;
        dict.set_item("single_comments", 0u32)?;
        Ok(dict)
    }
}

fn analyze_source(source: &str) -> Result<RawCounts, String> {
    let loc = if source.is_empty() {
        0
    } else {
        source.lines().count() as u32
    };

    let blank = source
        .lines()
        .filter(|line| line.trim().is_empty())
        .count() as u32;

    let sloc = loc.saturating_sub(blank);
    let comments = count_comment_tokens(source)?;

    Ok(RawCounts {
        loc,
        sloc,
        comments,
        blank,
    })
}

fn count_comment_tokens(source: &str) -> Result<u32, String> {
    let mut lexer: Lexer<'_> = lex(source, Mode::Module);
    let mut comments = 0u32;

    loop {
        match lexer.next_token() {
            TokenKind::EndOfFile => break,
            TokenKind::Comment => comments += 1,
            _ => {}
        }
    }

    let errors = lexer.finish();
    if errors.is_empty() {
        Ok(comments)
    } else {
        Err(errors
            .into_iter()
            .map(|err| err.to_string())
            .collect::<Vec<_>>()
            .join("; "))
    }
}

#[pyfunction]
pub fn harvest_raw_metrics(
    py: Python<'_>,
    entries: Vec<(String, String)>,
) -> PyResult<Vec<(String, Py<PyDict>)>> {
    let mut results = Vec::with_capacity(entries.len());

    for (name, source) in entries {
        match analyze_source(&source) {
            Ok(metrics) => {
                let dict = metrics.to_pydict(py)?;
                results.push((name, dict.unbind()));
            }
            Err(err) => {
                let dict = PyDict::new(py);
                dict.set_item("error", err)?;
                results.push((name, dict.unbind()));
            }
        }
    }

    Ok(results)
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(harvest_raw_metrics, module)?)?;
    Ok(())
}
