/// Order model
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub order_id: Option<i32>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub client_id: Option<i32>,

    pub action: OrderAction,
    pub total_quantity: f64,
    pub order_type: OrderType,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub lmt_price: Option<f64>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub aux_price: Option<f64>,

    #[serde(default = "default_tif")]
    pub time_in_force: TimeInForce,

    #[serde(default)]
    pub outside_rth: bool,

    #[serde(default)]
    pub hidden: bool,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub good_after_time: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub good_till_date: Option<String>,
}

fn default_tif() -> TimeInForce {
    TimeInForce::Day
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "UPPERCASE")]
pub enum OrderAction {
    #[serde(rename = "BUY")]
    Buy,
    #[serde(rename = "SELL")]
    Sell,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OrderType {
    #[serde(rename = "MKT")]
    Market,
    #[serde(rename = "LMT")]
    Limit,
    #[serde(rename = "STP")]
    Stop,
    #[serde(rename = "STP LMT")]
    StopLimit,
    #[serde(rename = "TRAIL")]
    Trail,
    #[serde(rename = "TRAIL LIMIT")]
    TrailLimit,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OrderStatus {
    PendingSubmit,
    PendingCancel,
    PreSubmitted,
    Submitted,
    Cancelled,
    Filled,
    Inactive,
    PendingReject,
    Rejected,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "UPPERCASE")]
pub enum TimeInForce {
    #[serde(rename = "DAY")]
    Day,
    #[serde(rename = "GTC")]
    Gtc,
    #[serde(rename = "IOC")]
    Ioc,
    #[serde(rename = "GTD")]
    Gtd,
}

impl Order {
    pub fn new(action: OrderAction, quantity: f64, order_type: OrderType) -> Self {
        Self {
            order_id: None,
            client_id: None,
            action,
            total_quantity: quantity,
            order_type,
            lmt_price: None,
            aux_price: None,
            time_in_force: TimeInForce::Day,
            outside_rth: false,
            hidden: false,
            good_after_time: None,
            good_till_date: None,
        }
    }

    pub fn with_limit_price(mut self, price: f64) -> Self {
        self.lmt_price = Some(price);
        self
    }

    pub fn with_stop_price(mut self, price: f64) -> Self {
        self.aux_price = Some(price);
        self
    }

    pub fn with_tif(mut self, tif: TimeInForce) -> Self {
        self.time_in_force = tif;
        self
    }
}
