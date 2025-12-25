use crate::error::Result;
/// Request/Response handler utilities
use serde_json::Value;

pub fn parse_tool_request(request: &Value) -> Result<(String, Value)> {
    // Parse tool name and parameters from request
    Ok(("".into(), Value::Null))
}

pub fn format_response(success: bool, data: Option<Value>, error: Option<String>) -> Value {
    serde_json::json!({
        "success": success,
        "data": data,
        "error": error,
        "timestamp": chrono::Utc::now().to_rfc3339()
    })
}
