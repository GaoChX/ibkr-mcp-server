/// Contract model
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contract {
    pub symbol: String,
    pub sec_type: SecType,

    #[serde(default = "default_exchange")]
    pub exchange: String,

    #[serde(default = "default_currency")]
    pub currency: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub local_symbol: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub con_id: Option<i32>,

    // Options fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub strike: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub right: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub expiry: Option<String>,

    // Futures fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_trade_date: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub multiplier: Option<i32>,
}

fn default_exchange() -> String {
    "SMART".to_string()
}

fn default_currency() -> String {
    "USD".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "UPPERCASE")]
pub enum SecType {
    #[serde(rename = "STK")]
    Stock,
    #[serde(rename = "OPT")]
    Option,
    #[serde(rename = "FUT")]
    Future,
    #[serde(rename = "CASH")]
    Forex,
    #[serde(rename = "IND")]
    Index,
    #[serde(rename = "CFD")]
    CFD,
    #[serde(rename = "BOND")]
    Bond,
    #[serde(rename = "WAR")]
    Warrant,
    #[serde(rename = "CMDTY")]
    Commodity,
}

impl Default for Contract {
    fn default() -> Self {
        Self {
            symbol: String::new(),
            sec_type: SecType::Stock,
            exchange: default_exchange(),
            currency: default_currency(),
            local_symbol: None,
            con_id: None,
            strike: None,
            right: None,
            expiry: None,
            last_trade_date: None,
            multiplier: None,
        }
    }
}

impl Contract {
    pub fn new(symbol: impl Into<String>, sec_type: SecType) -> Self {
        Self {
            symbol: symbol.into(),
            sec_type,
            ..Default::default()
        }
    }

    pub fn with_exchange(mut self, exchange: impl Into<String>) -> Self {
        self.exchange = exchange.into();
        self
    }

    pub fn with_currency(mut self, currency: impl Into<String>) -> Self {
        self.currency = currency.into();
        self
    }
}
