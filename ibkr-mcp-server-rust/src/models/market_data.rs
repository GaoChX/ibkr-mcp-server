use super::Contract;
use chrono::{DateTime, Utc};
/// Market data models
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TickData {
    pub symbol: String,
    pub tick_type: i32,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub price: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub size: Option<i32>,

    #[serde(default = "chrono::Utc::now")]
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BarData {
    pub date: DateTime<Utc>,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: i64,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub wap: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub count: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataRequest {
    pub contract: Contract,

    #[serde(default = "default_what_to_show")]
    pub what_to_show: String,

    #[serde(default = "default_bar_size")]
    pub bar_size: String,

    #[serde(default = "default_duration")]
    pub duration: String,

    #[serde(default = "default_use_rth")]
    pub use_rth: bool,
}

fn default_what_to_show() -> String {
    "TRADES".to_string()
}

fn default_bar_size() -> String {
    "1 min".to_string()
}

fn default_duration() -> String {
    "1 D".to_string()
}

fn default_use_rth() -> bool {
    true
}
