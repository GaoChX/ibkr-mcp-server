use ibkr_mcp_server::{IBKRClient, Result, Settings};

#[tokio::test]
async fn test_settings_loading() {
    let settings = Settings::new();
    assert!(settings.is_ok());

    let settings = settings.unwrap();
    assert_eq!(settings.ibkr.host, "127.0.0.1");
    assert_eq!(settings.ibkr.port, 4002);
}

#[tokio::test]
async fn test_ibkr_client_creation() {
    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    // Client should be created successfully
    assert!(!client.is_connected().await);
}

#[tokio::test]
async fn test_ibkr_client_connect() -> Result<()> {
    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    // Test mock connection
    client.connect().await?;
    assert!(client.is_connected().await);

    Ok(())
}

#[tokio::test]
async fn test_get_account_summary() -> Result<()> {
    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    client.connect().await?;
    let summary = client.get_account_summary().await?;

    assert!(!summary.is_empty());
    assert_eq!(summary.len(), 3);

    Ok(())
}

#[tokio::test]
async fn test_get_positions() -> Result<()> {
    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    client.connect().await?;
    let positions = client.get_positions().await?;

    assert_eq!(positions.len(), 2);
    assert_eq!(positions[0].contract.symbol, "AAPL");
    assert_eq!(positions[1].contract.symbol, "MSFT");

    Ok(())
}

#[tokio::test]
async fn test_place_order() -> Result<()> {
    use ibkr_mcp_server::models::{Contract, Order, OrderAction, OrderType, SecType};

    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    client.connect().await?;

    let contract = Contract::new("AAPL", SecType::Stock);
    let order = Order::new(OrderAction::Buy, 100.0, OrderType::Market);

    let order_id = client.place_order(&contract, &order).await?;
    assert!(order_id >= 1000);

    Ok(())
}

#[tokio::test]
async fn test_cancel_order() -> Result<()> {
    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    client.connect().await?;

    let result = client.cancel_order(1001).await?;
    assert!(result);

    Ok(())
}

#[tokio::test]
async fn test_get_market_data() -> Result<()> {
    use ibkr_mcp_server::models::{Contract, SecType};

    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    client.connect().await?;

    let contract = Contract::new("AAPL", SecType::Stock);
    let data = client.get_market_data(&contract).await?;

    assert!(data["symbol"].as_str().unwrap() == "AAPL");
    assert!(data["last"].as_f64().is_some());

    Ok(())
}

#[tokio::test]
async fn test_not_connected_error() {
    use ibkr_mcp_server::IBKRMCPError;

    let settings = Settings::new().unwrap();
    let client = IBKRClient::new(settings.ibkr);

    // Should fail without connection
    let result = client.get_account_summary().await;
    assert!(result.is_err());

    if let Err(IBKRMCPError::NotConnected) = result {
        // Expected error
    } else {
        panic!("Expected NotConnected error");
    }
}
