//! IBKR MCP Server Library
//!
//! A high-performance Interactive Brokers MCP server implementation in Rust.

pub mod config;
pub mod error;
pub mod ibkr;
pub mod mcp;
pub mod models;
pub mod utils;

pub use config::Settings;
pub use error::{IBKRMCPError, Result};
pub use ibkr::IBKRClient;
pub use mcp::MCPServer;

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert!(!VERSION.is_empty());
    }
}
