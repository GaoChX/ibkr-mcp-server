use config::{Config, ConfigError, Environment};
/// Application settings and configuration
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Settings {
    pub ibkr: IBKRConfig,
    pub mcp: MCPConfig,
    pub logging: LoggingConfig,
    #[serde(default = "default_environment")]
    pub environment: String,
}

fn default_environment() -> String {
    "development".to_string()
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct IBKRConfig {
    #[serde(default = "default_ibkr_host")]
    pub host: String,

    #[serde(default = "default_ibkr_port")]
    pub port: u16,

    #[serde(default = "default_client_id")]
    pub client_id: i32,

    #[serde(default)]
    pub readonly: bool,

    #[serde(default = "default_timeout")]
    pub timeout: u64,
}

fn default_ibkr_host() -> String {
    "127.0.0.1".to_string()
}

fn default_ibkr_port() -> u16 {
    4002
}

fn default_client_id() -> i32 {
    1
}

fn default_timeout() -> u64 {
    30
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct MCPConfig {
    #[serde(default = "default_mcp_host")]
    pub host: String,

    #[serde(default = "default_mcp_port")]
    pub port: u16,

    #[serde(default = "default_max_connections")]
    pub max_connections: usize,
}

fn default_mcp_host() -> String {
    "0.0.0.0".to_string()
}

fn default_mcp_port() -> u16 {
    8080
}

fn default_max_connections() -> usize {
    100
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct LoggingConfig {
    #[serde(default = "default_log_level")]
    pub level: String,

    #[serde(default = "default_log_format")]
    pub format: String,
}

fn default_log_level() -> String {
    "info".to_string()
}

fn default_log_format() -> String {
    "pretty".to_string()
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        // 加载 .env 文件
        dotenvy::dotenv().ok();

        let config = Config::builder()
            // 默认值
            .set_default("ibkr.host", "127.0.0.1")?
            .set_default("ibkr.port", 4002)?
            .set_default("ibkr.client_id", 1)?
            .set_default("ibkr.readonly", false)?
            .set_default("ibkr.timeout", 30)?
            .set_default("mcp.host", "0.0.0.0")?
            .set_default("mcp.port", 8080)?
            .set_default("mcp.max_connections", 100)?
            .set_default("logging.level", "info")?
            .set_default("logging.format", "pretty")?
            .set_default("environment", "development")?
            // 从环境变量加载
            .add_source(
                Environment::with_prefix("IBKR")
                    .separator("__")
                    .try_parsing(true),
            )
            .build()?;

        config.try_deserialize()
    }

    pub fn is_production(&self) -> bool {
        self.environment.to_lowercase() == "production"
    }
}
