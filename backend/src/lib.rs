use pyo3::prelude::*;

mod cognitive;
mod cyclomatic;
mod files;
mod git;
mod halstead;
mod maintainability;
mod raw;
pub mod storage;

#[pymodule]
fn backend(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    files::register(module)?;
    git::register(module)?;
    storage::register(module)?;
    Ok(())
}
