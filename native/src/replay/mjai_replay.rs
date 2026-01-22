use pyo3::prelude::*;

#[pyclass]
pub struct MjaiReplay {}

#[pymethods]
impl MjaiReplay {
    #[new]
    pub fn new() -> Self {
        MjaiReplay {}
    }
}
