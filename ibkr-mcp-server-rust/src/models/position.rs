use super::Contract;
/// Position model
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub account: String,
    pub contract: Contract,
    pub position: f64,
    pub avg_cost: f64,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_price: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_value: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub unrealized_pnl: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub realized_pnl: Option<f64>,
}

impl Position {
    pub fn new(account: String, contract: Contract, position: f64, avg_cost: f64) -> Self {
        Self {
            account,
            contract,
            position,
            avg_cost,
            market_price: None,
            market_value: None,
            unrealized_pnl: None,
            realized_pnl: None,
        }
    }
}
