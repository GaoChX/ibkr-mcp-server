use chrono::{DateTime, Utc};
/// Response models
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPResponse<T> {
    pub success: bool,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,

    #[serde(default = "chrono::Utc::now")]
    pub timestamp: DateTime<Utc>,
}

impl<T> MCPResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            message: None,
            data: Some(data),
            error: None,
            timestamp: Utc::now(),
        }
    }

    pub fn error(error: impl Into<String>) -> Self {
        Self {
            success: false,
            message: None,
            data: None,
            error: Some(error.into()),
            timestamp: Utc::now(),
        }
    }

    pub fn with_message(mut self, message: impl Into<String>) -> Self {
        self.message = Some(message.into());
        self
    }
}
