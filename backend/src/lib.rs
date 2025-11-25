use pyo3::prelude::*;

mod cyclomatic;
mod files;
mod halstead;
mod maintainability;
mod parallel;
mod raw;

#[pymodule]
fn backend(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    raw::register(module)?;
    cyclomatic::register(module)?;
    halstead::register(module)?;
    maintainability::register(module)?;
    files::register(module)?;
    parallel::register(module)?;
    Ok(())
}
