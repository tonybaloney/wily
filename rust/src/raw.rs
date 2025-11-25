use std::mem;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};
use ruff_python_parser::lexer::lex;
use ruff_python_parser::{Mode, TokenKind};

#[derive(Debug, Default, Clone, Copy)]
struct RawCounts {
    loc: u32,
    lloc: u32,
    sloc: u32,
    comments: u32,
    blank: u32,
    multi: u32,
    single_comments: u32,
}

impl RawCounts {
    fn to_pydict<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("loc", self.loc)?;
        dict.set_item("lloc", self.lloc)?;
        dict.set_item("sloc", self.sloc)?;
        dict.set_item("comments", self.comments)?;
        dict.set_item("blank", self.blank)?;
        dict.set_item("multi", self.multi)?;
        dict.set_item("single_comments", self.single_comments)?;
        Ok(dict)
    }
}

fn analyze_source(source: &str) -> Result<RawCounts, String> {
    let line_table = LineTable::new(source);
    if line_table.is_empty() {
        return Ok(RawCounts::default());
    }

    let lex_summary = tokenize_source(source)?;
    let docstring_stats = detect_docstrings(&lex_summary, &line_table);

    let mut blank = docstring_stats.blank_lines;
    for idx in 0..line_table.len() {
        if docstring_stats.mask[idx] {
            continue;
        }
        if line_table.line_text(idx).trim().is_empty() {
            blank += 1;
        }
    }

    let mut single_comments = docstring_stats.single_line;
    for idx in 0..line_table.len() {
        if docstring_stats.mask[idx] {
            continue;
        }
        let trimmed = line_table.line_text(idx).trim_start();
        if !trimmed.is_empty() && trimmed.starts_with('#') {
            single_comments += 1;
        }
    }

    let loc = line_table.len() as u32;
    let sloc = loc.saturating_sub(blank + docstring_stats.multi_line + single_comments);

    Ok(RawCounts {
        loc,
        lloc: lex_summary.lloc,
        sloc,
        comments: lex_summary.comment_count,
        blank,
        multi: docstring_stats.multi_line,
        single_comments,
    })
}

#[derive(Clone, Copy)]
struct SimpleToken {
    kind: TokenKind,
}

struct LexSummary {
    logical_lines: Vec<Vec<SimpleToken>>,
    line_numbers: Vec<usize>,
    comment_count: u32,
    lloc: u32,
}

fn tokenize_source(source: &str) -> Result<LexSummary, String> {
    let mut lexer = lex(source, Mode::Module);
    let mut logical_lines: Vec<Vec<SimpleToken>> = Vec::new();
    let mut current_line: Vec<SimpleToken> = Vec::new();
    let mut comment_count = 0u32;
    let mut line_numbers: Vec<usize> = Vec::new();
    let mut current_line_number = 1usize;

    loop {
        let kind = lexer.next_token();
        if matches!(kind, TokenKind::Comment) {
            comment_count += 1;
        }
        current_line.push(SimpleToken { kind });

        if matches!(kind, TokenKind::Newline | TokenKind::EndOfFile) {
            logical_lines.push(mem::take(&mut current_line));
            line_numbers.push(current_line_number);
            if matches!(kind, TokenKind::Newline) {
                current_line_number += 1;
            }
        }

        if matches!(kind, TokenKind::EndOfFile) {
            break;
        }
    }

    let errors = lexer.finish();
    if !errors.is_empty() {
        return Err(
            errors
                .into_iter()
                .map(|err| err.to_string())
                .collect::<Vec<_>>()
                .join("; "),
        );
    }

    let lloc = logical_lines
        .iter()
        .map(|line| count_logical_line(line))
        .sum();

    Ok(LexSummary {
        logical_lines,
        line_numbers,
        comment_count,
        lloc,
    })
}

struct LineTable<'a> {
    texts: Vec<&'a str>,
}

impl<'a> LineTable<'a> {
    fn new(source: &'a str) -> Self {
        let mut texts = Vec::new();
        let bytes = source.as_bytes();
        let mut line_start = 0usize;
        let mut idx = 0usize;

        while idx < bytes.len() {
            match bytes[idx] {
                b'\n' => {
                    texts.push(&source[line_start..idx]);
                    idx += 1;
                    line_start = idx;
                }
                b'\r' => {
                    texts.push(&source[line_start..idx]);
                    idx += 1;
                    if idx < bytes.len() && bytes[idx] == b'\n' {
                        idx += 1;
                    }
                    line_start = idx;
                }
                _ => idx += 1,
            }
        }

        if line_start < source.len() {
            texts.push(&source[line_start..source.len()]);
        }

        Self { texts }
    }

    fn is_empty(&self) -> bool {
        self.texts.is_empty()
    }

    fn len(&self) -> usize {
        self.texts.len()
    }

    fn line_text(&self, idx: usize) -> &str {
        self.texts[idx]
    }

}

struct DocstringStats {
    mask: Vec<bool>,
    multi_line: u32,
    blank_lines: u32,
    single_line: u32,
}

fn detect_docstrings<'a>(summary: &LexSummary, lines: &LineTable<'a>) -> DocstringStats {
    let mut mask = vec![false; lines.len()];
    let mut multi = 0u32;
    let mut blank = 0u32;
    let mut single = 0u32;

    for (tokens, &line_number) in summary.logical_lines.iter().zip(summary.line_numbers.iter()) {
        if !is_docstring_candidate(tokens) {
            continue;
        }

        match docstring_extent(lines, line_number) {
            DocstringExtent::Single(line) => {
                if line == 0 || line > lines.len() {
                    continue;
                }
                mask[line - 1] = true;
                single += 1;
            }
            DocstringExtent::Multi { start, end } => {
                let bounded_end = end.min(lines.len());
                let bounded_start = start.min(lines.len());
                if bounded_start == 0 {
                    continue;
                }
                for line in bounded_start..=bounded_end {
                    mask[line - 1] = true;
                    let text = lines.line_text(line - 1);
                    if text.trim().is_empty() {
                        blank += 1;
                    } else {
                        multi += 1;
                    }
                }
            }
        }
    }

    DocstringStats {
        mask,
        multi_line: multi,
        blank_lines: blank,
        single_line: single,
    }
}

fn is_docstring_candidate(tokens: &[SimpleToken]) -> bool {
    let mut iter = tokens.iter().filter(|token| {
        !matches!(
            token.kind,
            TokenKind::Indent
                | TokenKind::Dedent
                | TokenKind::Newline
                | TokenKind::NonLogicalNewline
                | TokenKind::EndOfFile
        )
    });

    matches!(iter.next(), Some(token) if token.kind == TokenKind::String) && iter.next().is_none()
}

enum DocstringExtent {
    Single(usize),
    Multi { start: usize, end: usize },
}

fn docstring_extent(lines: &LineTable<'_>, start_line: usize) -> DocstringExtent {
    if start_line == 0 || start_line > lines.len() {
        return DocstringExtent::Single(start_line);
    }

    let text = lines.line_text(start_line - 1);
    let trimmed = text.trim_start();
    let (prefix_len, is_raw) = parse_string_prefix(trimmed);
    let rest = &trimmed[prefix_len..];

    if rest.len() < 3 {
        return DocstringExtent::Single(start_line);
    }

    let bytes = rest.as_bytes();
    let quote = bytes[0];
    if quote != b'"' && quote != b'\'' {
        return DocstringExtent::Single(start_line);
    }

    let is_triple = bytes.len() >= 3 && bytes[0] == bytes[1] && bytes[1] == bytes[2];
    if !is_triple {
        return DocstringExtent::Single(start_line);
    }

    if closing_triple_in_slice(&rest[3..], quote, is_raw) {
        return DocstringExtent::Single(start_line);
    }

    let mut line = start_line + 1;
    while line <= lines.len() {
        if closing_triple_in_slice(lines.line_text(line - 1), quote, is_raw) {
            return DocstringExtent::Multi { start: start_line, end: line };
        }
        line += 1;
    }

    DocstringExtent::Multi {
        start: start_line,
        end: lines.len().max(start_line),
    }
}

fn parse_string_prefix(text: &str) -> (usize, bool) {
    let mut idx = 0usize;
    let mut is_raw = false;
    let bytes = text.as_bytes();

    while idx < bytes.len() {
        let lower = bytes[idx].to_ascii_lowercase();
        if matches!(lower, b'r' | b'u' | b'f' | b'b' | b't') {
            if lower == b'r' {
                is_raw = true;
            }
            idx += 1;
        } else {
            break;
        }
    }

    (idx, is_raw)
}

fn closing_triple_in_slice(text: &str, quote: u8, is_raw: bool) -> bool {
    let bytes = text.as_bytes();
    if bytes.len() < 3 {
        return false;
    }

    let pattern = [quote, quote, quote];
    let mut idx = 0usize;
    while idx + 3 <= bytes.len() {
        if bytes[idx..idx + 3] == pattern {
            if is_raw {
                return true;
            }

            let mut escapes = 0usize;
            let mut pos = idx;
            while pos > 0 && bytes[pos - 1] == b'\\' {
                escapes += 1;
                pos -= 1;
            }

            if escapes % 2 == 0 {
                return true;
            }
        }
        idx += 1;
    }

    false
}

fn count_logical_line(tokens: &[SimpleToken]) -> u32 {
    if tokens.is_empty() {
        return 0;
    }

    let mut total = 0u32;
    let mut start = 0usize;

    for (idx, token) in tokens.iter().enumerate() {
        if token.kind == TokenKind::Semi {
            total += count_logical_segment(&tokens[start..idx]);
            start = idx + 1;
        }
    }

    total + count_logical_segment(&tokens[start..])
}

fn count_logical_segment(tokens: &[SimpleToken]) -> u32 {
    if tokens.is_empty() {
        return 0;
    }

    let processed: Vec<TokenKind> = tokens
        .iter()
        .map(|token| token.kind)
        .filter(|kind| {
            !matches!(
                kind,
                TokenKind::Comment
                    | TokenKind::Newline
                    | TokenKind::NonLogicalNewline
                    | TokenKind::Indent
                    | TokenKind::Dedent
            )
        })
        .collect();

    if processed.is_empty() {
        return 0;
    }

    if let Some(idx) = processed.iter().rposition(|kind| *kind == TokenKind::Colon) {
        let trailing_has_code = processed[idx + 1..]
            .iter()
            .any(|kind| !matches!(kind, TokenKind::EndOfFile));
        return if trailing_has_code { 2 } else { 1 };
    }

    if processed
        .iter()
        .any(|kind| !matches!(kind, TokenKind::EndOfFile))
    {
        1
    } else {
        0
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
