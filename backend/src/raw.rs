//! Raw metrics calculation using Ruff's parser infrastructure.
//!
//! This module calculates raw source code metrics compatible with Radon:
//! - loc: Total lines of code
//! - lloc: Logical lines of code  
//! - sloc: Source lines of code (excluding blanks, comments, docstrings)
//! - comments: Total comment count
//! - multi: Multi-line string/docstring lines
//! - blank: Blank lines
//! - single_comments: Lines containing only comments

use pyo3::prelude::*;
use ruff_python_ast::ModModule;
use ruff_python_parser::{TokenKind};
use ruff_python_trivia::CommentRanges;
use ruff_source_file::{LineIndex, OneIndexed};
use ruff_text_size::{Ranged, TextRange};

#[derive(Debug, Default, Clone, Copy, IntoPyObject)]
pub struct RawCounts {
    pub loc: usize,
    pub lloc: usize,
    pub sloc: usize,
    pub comments: usize,
    pub blank: usize,
    pub multi: usize,
    pub single_comments: usize,
}

pub fn analyze(parsed: &ruff_python_parser::Parsed<ModModule>, line_index: &LineIndex, source: &str) -> RawCounts {
    let tokens = parsed.tokens();
    let comment_ranges: CommentRanges = tokens.into();

    // Count total lines
    let loc = line_index.line_count();
    if loc == 0 {
        return RawCounts::default();
    }

    // Track which lines are covered by multi-line strings
    let mut multiline_string_lines = vec![false; loc as usize];
    // Track single-line docstrings (string-only logical lines)
    let mut single_line_docstring_lines = vec![false; loc as usize];

    // Track comment count
    let comments = comment_ranges.len();

    // Process tokens to find strings and identify single-line docstrings
    // Group tokens by logical line (ending at Newline/EOF)
    let mut current_line_tokens: Vec<(TokenKind, usize, usize)> = Vec::new();

    for token in tokens.iter() {
        let kind = token.kind();
        let range = token.range();
        let start_line = line_index.line_index(range.start()).to_zero_indexed();
        let end_line = line_index.line_index(range.end()).to_zero_indexed();

        // Track multi-line strings
        if kind == TokenKind::String && end_line > start_line {
            for line in multiline_string_lines
                .iter_mut()
                .take(end_line + 1)
                .skip(start_line)
            {
                *line = true;
            }
        }

        current_line_tokens.push((kind, start_line, end_line));

        if matches!(kind, TokenKind::Newline | TokenKind::EndOfFile) {
            // Check if this logical line is a single-line docstring
            if is_single_line_docstring(&current_line_tokens) {
                // Find the line with the string
                for &(k, start, end) in &current_line_tokens {
                    if k == TokenKind::String && start == end && start < loc as usize {
                        single_line_docstring_lines[start] = true;
                    }
                }
            }
            current_line_tokens.clear();
        }
    }

    // Count blank lines, multi-line string lines, and single-comment lines
    let mut blank = 0usize;
    let mut multi = 0usize;
    let mut single_comments = 0usize;

    for line_num in 0..loc as usize {
        let line_idx = OneIndexed::from_zero_indexed(line_num);
        let line_start = line_index.line_start(line_idx, source);
        let line_end = line_index.line_end(line_idx, source);
        let line_range = TextRange::new(line_start, line_end);
        let line_text = &source[line_range];
        let trimmed = line_text.trim();

        if multiline_string_lines[line_num] {
            // Line is part of a multi-line string
            if trimmed.is_empty() {
                blank += 1;
            } else {
                multi += 1;
            }
        } else if single_line_docstring_lines[line_num] {
            // Single-line docstring counts as single_comments in Radon
            single_comments += 1;
        } else if trimmed.is_empty() {
            blank += 1;
        } else if trimmed.starts_with('#') {
            single_comments += 1;
        }
    }

    // Calculate lloc from logical lines
    let lloc = count_logical_lines(tokens);

    // sloc = loc - blank - multi - single_comments
    let sloc = loc.saturating_sub(blank + multi + single_comments);

    RawCounts {
        loc,
        lloc,
        sloc,
        comments,
        blank,
        multi,
        single_comments,
    }
}

/// Check if a logical line contains only a single-line string (docstring)
fn is_single_line_docstring(tokens: &[(TokenKind, usize, usize)]) -> bool {
    // Filter out non-semantic tokens
    let significant: Vec<_> = tokens
        .iter()
        .filter(|(k, _, _)| {
            !matches!(
                k,
                TokenKind::Indent
                    | TokenKind::Dedent
                    | TokenKind::Newline
                    | TokenKind::NonLogicalNewline
                    | TokenKind::EndOfFile
            )
        })
        .collect();

    // Must be exactly one token, and it must be a single-line string
    if significant.len() != 1 {
        return false;
    }

    let (kind, start_line, end_line) = significant[0];
    *kind == TokenKind::String && start_line == end_line
}

/// Count logical lines of code using token stream.
/// A logical line ends at Newline tokens (not NonLogicalNewline).
/// Each logical line can contain multiple statements separated by semicolons.
fn count_logical_lines(tokens: &ruff_python_parser::Tokens) -> usize {
    let mut lloc = 0usize;
    let mut current_line: Vec<TokenKind> = Vec::new();

    for token in tokens.iter() {
        let kind = token.kind();
        current_line.push(kind);

        if matches!(kind, TokenKind::Newline | TokenKind::EndOfFile) {
            lloc += count_logical_line(&current_line);
            current_line.clear();
        }
    }

    lloc
}

/// Count logical statements in a single logical line.
/// Semicolons separate multiple statements on one line.
/// Colons followed by code (like `if x: pass`) count as 2.
fn count_logical_line(tokens: &[TokenKind]) -> usize {
    if tokens.is_empty() {
        return 0;
    }

    let mut total = 0usize;
    let mut start = 0usize;

    for (idx, &kind) in tokens.iter().enumerate() {
        if kind == TokenKind::Semi {
            total += count_logical_segment(&tokens[start..idx]);
            start = idx + 1;
        }
    }

    total + count_logical_segment(&tokens[start..])
}

/// Count a single segment (between semicolons) as 0, 1, or 2 logical lines.
fn count_logical_segment(tokens: &[TokenKind]) -> usize {
    // Filter out non-code tokens
    let code_tokens: Vec<TokenKind> = tokens
        .iter()
        .copied()
        .filter(|kind| {
            !matches!(
                kind,
                TokenKind::Comment
                    | TokenKind::Newline
                    | TokenKind::NonLogicalNewline
                    | TokenKind::Indent
                    | TokenKind::Dedent
                    | TokenKind::EndOfFile
            )
        })
        .collect();

    if code_tokens.is_empty() {
        return 0;
    }

    // Check for colon with trailing code (e.g., `if x: pass`)
    if let Some(colon_idx) = code_tokens.iter().rposition(|&k| k == TokenKind::Colon) {
        let has_trailing_code = code_tokens[colon_idx + 1..].iter().any(|_| true);
        return if has_trailing_code { 2 } else { 1 };
    }

    1
}
