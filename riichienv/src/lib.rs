use pyo3::prelude::*;

mod types;
mod agari;
mod yaku;
mod score;
mod agari_calculator;
mod tests;

mod parser;

#[pymodule]
fn _riichienv(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<types::Hand>()?;
    m.add_class::<types::Meld>()?;
    m.add_class::<types::MeldType>()?;
    m.add_class::<types::Conditions>()?;
    m.add_class::<types::Agari>()?;
    m.add_class::<score::Score>()?;
    m.add_class::<agari_calculator::AgariCalculator>()?;
    m.add_function(wrap_pyfunction!(agari::is_agari, m)?)?;
    m.add_function(wrap_pyfunction!(score::calculate_score, m)?)?;
    m.add_function(wrap_pyfunction!(parser::parse_hand, m)?)?;
    Ok(())
}
