/// Custom error types for IBKR MCP Server
use thiserror::Error;

#[derive(Error, Debug)]
pub enum IBKRMCPError {
    #[error("IBKR connection error: {0}")]
    Connection(String),
    
    #[error("IBKR order error: {0}")]
    Order(String),
    
    #[error("Market data error: {0}")]
    MarketData(String),
    
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("MCP protocol error: {0}")]
    Protocol(String),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Timeout error")]
    Timeout,
    
    #[error("Not connected to IBKR")]
    NotConnected,
    
    #[error("Invalid parameter: {0}")]
    InvalidParameter(String),
}

pub type Result<T> = std::result::Result<T, IBKRMCPError>;
