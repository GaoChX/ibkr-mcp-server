/// MCP Server implementation
use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde_json::{json, Value};
use std::sync::Arc;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::{error, info};

use crate::{
    config::Settings,
    error::{IBKRMCPError, Result},
    ibkr::IBKRClient,
};

// Shared state for Axum handlers
struct ServerState {
    ibkr_client: Arc<IBKRClient>,
    settings: Settings,
}

pub struct MCPServer {
    ibkr_client: Arc<IBKRClient>,
    settings: Settings,
}

impl MCPServer {
    pub fn new(settings: Settings) -> Self {
        let ibkr_client = Arc::new(IBKRClient::new(settings.ibkr.clone()));

        Self {
            ibkr_client,
            settings,
        }
    }

    pub async fn run(self) -> Result<()> {
        let ibkr_client = Arc::clone(&self.ibkr_client);
        let settings = self.settings.clone();

        // Connect to IBKR
        info!("Connecting to IBKR...");
        if let Err(e) = ibkr_client.connect().await {
            error!("Failed to connect to IBKR: {}", e);
            info!("Server will start without IBKR connection");
        }

        // Create Arc wrapper for shared state
        let server_state = Arc::new(ServerState {
            ibkr_client,
            settings: settings.clone(),
        });

        // Build router
        let app = Router::new()
            .route("/health", get(health_check))
            .route("/mcp/tools", post(handle_tool_call))
            .route("/mcp/status", get(connection_status))
            // Standard MCP protocol endpoints
            .route("/mcp", post(handle_mcp_request))
            .route("/", post(handle_mcp_request))
            .layer(TraceLayer::new_for_http())
            .layer(CorsLayer::permissive())
            .with_state(server_state);

        // Start server
        let addr = format!("{}:{}", settings.mcp.host, settings.mcp.port);
        info!("Starting MCP server on {}", addr);

        let listener = tokio::net::TcpListener::bind(&addr)
            .await
            .map_err(|e| IBKRMCPError::Io(e))?;

        info!("🚀 IBKR MCP Server (Rust) listening on {}", addr);

        axum::serve(listener, app)
            .await
            .map_err(|e| IBKRMCPError::Connection(e.to_string()))?;

        Ok(())
    }

    pub async fn shutdown(&self) -> Result<()> {
        info!("Shutting down server...");
        self.ibkr_client.disconnect().await?;
        info!("Server shutdown complete");
        Ok(())
    }
}

// Handle standard MCP protocol requests
async fn handle_mcp_request(
    State(server): State<Arc<ServerState>>,
    Json(request): Json<Value>,
) -> impl IntoResponse {
    info!("Received MCP request: {:?}", request);

    // Extract method from request
    let method = request["method"].as_str().unwrap_or("");

    let response = match method {
        "initialize" => {
            // MCP initialization request
            json!({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "ibkr-mcp-server",
                        "version": crate::VERSION
                    }
                }
            })
        }
        "initialized" => {
            // MCP initialized notification - no response needed for notifications
            // Just acknowledge we received it
            info!("MCP client initialized");
            // For notifications, we should return 204 No Content or an empty success
            return (StatusCode::NO_CONTENT, Json(json!({})));
        }
        "tools/list" => {
            // Return list of available tools
            json!({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "get_account_summary",
                            "description": "Get account summary including balance and portfolio information",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_positions",
                            "description": "Get current positions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "place_order",
                            "description": "Place a new order",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "symbol": { "type": "string" },
                                    "action": { "type": "string", "enum": ["BUY", "SELL"] },
                                    "quantity": { "type": "number" },
                                    "order_type": { "type": "string", "enum": ["MKT", "LMT", "STP"] }
                                },
                                "required": ["symbol", "action", "quantity"]
                            }
                        },
                        {
                            "name": "get_market_data",
                            "description": "Get real-time market data for a symbol",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "symbol": { "type": "string" }
                                },
                                "required": ["symbol"]
                            }
                        },
                        {
                            "name": "connection_status",
                            "description": "Check IBKR connection status",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            })
        }
        "tools/call" => {
            // Extract tool name and arguments
            let params = &request["params"];
            let tool_name = params["name"].as_str().unwrap_or("");
            let arguments = &params["arguments"];

            // Process the tool call inline
            let tool_result = process_tool_call(&server, tool_name, arguments).await;

            json!({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": tool_result
            })
        }
        _ => {
            json!({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": format!("Method not found: {}", method)
                }
            })
        }
    };

    (StatusCode::OK, Json(response))
}

// Health check endpoint
async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "ibkr-mcp-server-rust",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

// Connection status endpoint
async fn connection_status(State(server): State<Arc<ServerState>>) -> Json<Value> {
    let connected = server.ibkr_client.is_connected().await;

    Json(json!({
        "connected": connected,
        "host": server.settings.ibkr.host,
        "port": server.settings.ibkr.port,
        "client_id": server.settings.ibkr.client_id,
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

// Helper function to process tool calls
async fn process_tool_call(server: &ServerState, tool_name: &str, params: &Value) -> Value {
    match tool_name {
        "get_account_summary" => match server.ibkr_client.get_account_summary().await {
            Ok(data) => json!({
                "success": true,
                "data": data,
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
            Err(e) => json!({
                "success": false,
                "error": e.to_string(),
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
        },
        "get_positions" => match server.ibkr_client.get_positions().await {
            Ok(positions) => json!({
                "success": true,
                "data": positions,
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
            Err(e) => json!({
                "success": false,
                "error": e.to_string(),
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
        },
        "place_order" => {
            // Extract order parameters
            let symbol = params["symbol"].as_str().unwrap_or("");
            let sec_type = params["sec_type"].as_str().unwrap_or("STK");
            let action = params["action"].as_str().unwrap_or("BUY");
            let quantity = params["quantity"].as_f64().unwrap_or(0.0);
            let order_type = params["order_type"].as_str().unwrap_or("MKT");
            let limit_price = params["limit_price"].as_f64();

            // Create contract and order
            use crate::models::{Contract, Order, OrderAction, OrderType as OT, SecType as ST};

            let contract = Contract::new(
                symbol,
                match sec_type {
                    "STK" => ST::Stock,
                    "OPT" => ST::Option,
                    "FUT" => ST::Future,
                    _ => ST::Stock,
                },
            );

            let mut order = Order::new(
                if action == "BUY" {
                    OrderAction::Buy
                } else {
                    OrderAction::Sell
                },
                quantity,
                match order_type {
                    "LMT" => OT::Limit,
                    "STP" => OT::Stop,
                    _ => OT::Market,
                },
            );

            if let Some(price) = limit_price {
                order = order.with_limit_price(price);
            }

            match server.ibkr_client.place_order(&contract, &order).await {
                Ok(order_id) => json!({
                    "success": true,
                    "data": {
                        "order_id": order_id,
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity
                    },
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
                Err(e) => json!({
                    "success": false,
                    "error": e.to_string(),
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
            }
        }
        "cancel_order" => {
            let order_id = params["order_id"].as_i64().unwrap_or(0) as i32;

            match server.ibkr_client.cancel_order(order_id).await {
                Ok(cancelled) => json!({
                    "success": true,
                    "data": {
                        "order_id": order_id,
                        "cancelled": cancelled
                    },
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
                Err(e) => json!({
                    "success": false,
                    "error": e.to_string(),
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
            }
        }
        "get_open_orders" => match server.ibkr_client.get_open_orders().await {
            Ok(orders) => json!({
                "success": true,
                "data": orders,
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
            Err(e) => json!({
                "success": false,
                "error": e.to_string(),
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
        },
        "get_market_data" => {
            let symbol = params["symbol"].as_str().unwrap_or("AAPL");
            let sec_type = params["sec_type"].as_str().unwrap_or("STK");

            use crate::models::{Contract, SecType as ST};
            let contract = Contract::new(
                symbol,
                match sec_type {
                    "STK" => ST::Stock,
                    _ => ST::Stock,
                },
            );

            match server.ibkr_client.get_market_data(&contract).await {
                Ok(data) => json!({
                    "success": true,
                    "data": data,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
                Err(e) => json!({
                    "success": false,
                    "error": e.to_string(),
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
            }
        }
        "get_historical_data" => {
            let symbol = params["symbol"].as_str().unwrap_or("AAPL");
            let duration = params["duration"].as_str().unwrap_or("1 D");
            let bar_size = params["bar_size"].as_str().unwrap_or("1 min");
            let what_to_show = params["what_to_show"].as_str().unwrap_or("TRADES");

            use crate::models::{Contract, SecType as ST};
            let contract = Contract::new(symbol, ST::Stock);

            match server
                .ibkr_client
                .get_historical_data(&contract, duration, bar_size, what_to_show)
                .await
            {
                Ok(bars) => json!({
                    "success": true,
                    "data": bars,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
                Err(e) => json!({
                    "success": false,
                    "error": e.to_string(),
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }),
            }
        }
        "reconnect" => match server.ibkr_client.reconnect().await {
            Ok(_) => json!({
                "success": true,
                "data": {
                    "reconnected": true
                },
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
            Err(e) => json!({
                "success": false,
                "error": e.to_string(),
                "timestamp": chrono::Utc::now().to_rfc3339()
            }),
        },
        "connection_status" => {
            let connected = server.ibkr_client.is_connected().await;
            json!({
                "success": true,
                "data": {
                    "connected": connected,
                    "host": server.settings.ibkr.host,
                    "port": server.settings.ibkr.port
                },
                "timestamp": chrono::Utc::now().to_rfc3339()
            })
        }
        _ => {
            json!({
                "success": false,
                "error": format!("Unknown tool: {}", tool_name),
                "timestamp": chrono::Utc::now().to_rfc3339()
            })
        }
    }
}

// Tool call handler
async fn handle_tool_call(
    State(server): State<Arc<ServerState>>,
    Json(request): Json<Value>,
) -> impl IntoResponse {
    info!("Received tool call: {:?}", request);

    // Extract tool name and parameters
    let tool_name = request["tool"].as_str().unwrap_or("");
    let params = &request["parameters"];

    let response = process_tool_call(&server, tool_name, params).await;

    (StatusCode::OK, Json(response))
}
