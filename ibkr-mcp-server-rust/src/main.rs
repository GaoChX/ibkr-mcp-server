//! IBKR MCP Server - Main Entry Point
//!
//! High-performance Interactive Brokers MCP server written in Rust

use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

use ibkr_mcp_server::{MCPServer, Result, Settings};

#[tokio::main]
async fn main() -> Result<()> {
    // Load environment variables from .env file
    dotenvy::dotenv().ok();

    // Initialize tracing
    init_tracing();

    // Print banner
    print_banner();

    // Load configuration
    let settings =
        Settings::new().map_err(|e| ibkr_mcp_server::IBKRMCPError::Config(e.to_string()))?;

    info!("Configuration loaded successfully");
    info!("Environment: {}", settings.environment);
    info!("IBKR: {}:{}", settings.ibkr.host, settings.ibkr.port);
    info!("MCP Server: {}:{}", settings.mcp.host, settings.mcp.port);

    // Create and run server
    let server = MCPServer::new(settings);

    // Setup graceful shutdown
    let shutdown_signal = async {
        tokio::signal::ctrl_c()
            .await
            .expect("Failed to install CTRL+C signal handler");
        info!("Shutdown signal received");
    };

    // Run server
    tokio::select! {
        result = server.run() => {
            if let Err(e) = result {
                eprintln!("Server error: {}", e);
                std::process::exit(1);
            }
        }
        _ = shutdown_signal => {
            info!("Shutting down gracefully...");
        }
    }

    Ok(())
}

fn init_tracing() {
    tracing_subscriber::registry()
        .with(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "ibkr_mcp_server=info,tower_http=debug,axum=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .init();
}

fn print_banner() {
    println!(
        r#"
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║        IBKR MCP Server (Rust Edition) 🦀            ║
    ║        High-Performance Trading Server               ║
    ║                                                      ║
    ║        Version: {}                              ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    "#,
        ibkr_mcp_server::VERSION
    );
}
