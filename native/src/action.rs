use pyo3::prelude::*;
use pyo3::types::{PyDict, PyDictMethods};
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::parser::tid_to_mjai;

#[pyclass(module = "riichienv._riichienv", eq, eq_int)]
#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Phase {
    WaitAct = 0,
    WaitResponse = 1,
}

#[pymethods]
impl Phase {
    fn __hash__(&self) -> i32 {
        *self as i32
    }
}

#[pyclass(module = "riichienv._riichienv", eq, eq_int)]
#[repr(i32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ActionType {
    Discard = 0,
    Chi = 1,
    Pon = 2,
    Daiminkan = 3,
    Ron = 4,
    Riichi = 5,
    Tsumo = 6,
    Pass = 7,
    Ankan = 8,
    Kakan = 9,
    KyushuKyuhai = 10,
}

#[pymethods]
impl ActionType {
    fn __hash__(&self) -> i32 {
        *self as i32
    }
}

#[pyclass(module = "riichienv._riichienv")]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Action {
    #[pyo3(get, set)]
    pub action_type: ActionType,
    #[pyo3(get, set)]
    pub tile: Option<u8>,
    pub consume_tiles: Vec<u8>,
}

#[pymethods]
impl Action {
    #[new]
    #[pyo3(signature = (r#type=ActionType::Pass, tile=None, consume_tiles=vec![]))]
    pub fn new(r#type: ActionType, tile: Option<u8>, consume_tiles: Vec<u8>) -> Self {
        let mut sorted_consume = consume_tiles;
        sorted_consume.sort();
        Self {
            action_type: r#type,
            tile,
            consume_tiles: sorted_consume,
        }
    }

    pub fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new(py);
        dict.set_item("type", self.action_type as i32)?;
        dict.set_item("tile", self.tile)?;

        let cons: Vec<u32> = self.consume_tiles.iter().map(|&x| x as u32).collect();
        dict.set_item("consume_tiles", cons)?;
        Ok(dict.unbind().into())
    }

    pub fn to_mjai(&self) -> PyResult<String> {
        let type_str = match self.action_type {
            ActionType::Discard => "dahai",
            ActionType::Chi => "chi",
            ActionType::Pon => "pon",
            ActionType::Daiminkan => "daiminkan",
            ActionType::Ankan => "ankan",
            ActionType::Kakan => "kakan",
            ActionType::Riichi => "reach",
            ActionType::Tsumo | ActionType::Ron => "hora",
            ActionType::KyushuKyuhai => "ryukyoku",
            ActionType::Pass => "none",
        };

        let mut data = serde_json::Map::new();
        data.insert("type".to_string(), Value::String(type_str.to_string()));

        if let Some(t) = self.tile {
            if self.action_type != ActionType::Tsumo
                && self.action_type != ActionType::Ron
                && self.action_type != ActionType::Riichi
            {
                data.insert("pai".to_string(), Value::String(tid_to_mjai(t)));
            }
        }

        if !self.consume_tiles.is_empty() {
            let cons: Vec<String> = self.consume_tiles.iter().map(|&t| tid_to_mjai(t)).collect();
            data.insert("consumed".to_string(), serde_json::to_value(cons).unwrap());
        }

        Ok(Value::Object(data).to_string())
    }

    fn __repr__(&self) -> String {
        format!(
            "Action(action_type={:?}, tile={:?}, consume_tiles={:?})",
            self.action_type, self.tile, self.consume_tiles
        )
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }

    #[getter]
    fn get_consume_tiles(&self) -> Vec<u32> {
        self.consume_tiles.iter().map(|&x| x as u32).collect()
    }

    #[setter]
    fn set_consume_tiles(&mut self, value: Vec<u8>) {
        self.consume_tiles = value;
    }
}
