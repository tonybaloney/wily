use pyo3::prelude::*;

mod cyclomatic;
mod raw;

#[pymodule]
fn _rust(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    raw::register(module)?;
    cyclomatic::register(module)?;
    Ok(())
}
