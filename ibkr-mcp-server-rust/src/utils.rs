/// Utility functions
use crate::error::Result;

/// Validate configuration parameters
pub fn validate_config(config: &crate::config::Settings) -> Result<()> {
    // Add validation logic
    Ok(())
}

/// Format duration string
pub fn format_duration(milliseconds: u64) -> String {
    if milliseconds < 1000 {
        format!("{}ms", milliseconds)
    } else {
        format!("{:.2}s", milliseconds as f64 / 1000.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_duration() {
        assert_eq!(format_duration(500), "500ms");
        assert_eq!(format_duration(1500), "1.50s");
    }
}
