use pyo3::prelude::*;

mod raw;

/// Example function implemented in Rust to demonstrate PyO3 integration.
#[pyfunction]
fn rust_add(a: i64, b: i64) -> PyResult<i64> {
    Ok(a + b)
}

/// PyO3 module definition exposed to Python as `wily._rust`.
#[pymodule]
fn _rust(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(rust_add, module)?)?;
    raw::register(module)?;
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
