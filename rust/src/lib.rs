use pyo3::prelude::*;

mod cyclomatic;
mod halstead;
mod raw;

#[pymodule]
fn _rust(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    raw::register(module)?;
    cyclomatic::register(module)?;
    halstead::register(module)?;
    Ok(())
}
