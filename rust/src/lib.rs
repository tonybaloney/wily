use pyo3::prelude::*;

mod raw;

#[pymodule]
fn _rust(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    raw::register(module)?;
    Ok(())
}
