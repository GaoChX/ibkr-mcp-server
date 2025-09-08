# IBKR MCP Server

An Interactive Brokers (IBKR) MCP server implementation based on FastMCP 2.0 and MCP StreamableHTTP, providing account management, trading operations, and market data query functionality.

## Features

- 🔗 **Connection Management**: Stable connection with IBKR TWS/Gateway
- 📊 **Account Information**: Query account summary, positions, and balances
- 💹 **Trading Operations**: Place orders, cancel orders, query order status
- 📈 **Market Data**: Real-time and historical market data retrieval
- 🛡️ **Type Safety**: Data validation using Pydantic
- ⚡ **Async Architecture**: High-performance asynchronous I/O operations
- 📝 **Rich Logging**: Structured logging
- 🔧 **Flexible Configuration**: Support for environment variables and configuration files

## Installation

### Install from Source

```bash
git clone https://github.com/yourusername/ibkr-mcp-server.git
cd ibkr-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

## Quick Start

### 1. Configure Environment

Create a `.env` file in the project root:

```env
# MCP Server Settings
MCP__HOST=0.0.0.0
MCP__PORT=8080

# IBKR Connection Settings
IBKR__HOST=127.0.0.1
IBKR__PORT=4002
IBKR__CLIENT_ID=1
IBKR__READONLY=false

# Logging Settings
LOGGING__LEVEL=INFO
```

### 2. Test Connection

```bash
# Test IBKR connection
python -m ibkr_mcp_server.cli test --host 127.0.0.1 --port 4002
```

### 3. Start Server

```bash
# Start server
python -m ibkr_mcp_server.cli serve

# Or with custom parameters
python -m ibkr_mcp_server.cli serve --host 0.0.0.0 --port 8080
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP__HOST` | `0.0.0.0` | MCP server listen address |
| `MCP__PORT` | `8080` | MCP server port |
| `IBKR__HOST` | `127.0.0.1` | IBKR TWS/Gateway address |
| `IBKR__PORT` | `4002` | IBKR TWS/Gateway port |
| `IBKR__CLIENT_ID` | `1` | IBKR client ID |
| `IBKR__READONLY` | `false` | Read-only mode |
| `LOGGING__LEVEL` | `INFO` | Logging level |

### IBKR Port Configuration

| Platform | Demo Port | Live Port |
|----------|-----------|-----------|
| TWS | 4002 | 7496 |
| Gateway | 4002 | 4001 |

## MCP Tools

The server provides 9 MCP tools:

### Account Management

- `get_account_summary`: Get account summary information
- `get_positions`: Get position information

### Trading Operations

- `place_order`: Place an order
- `cancel_order`: Cancel an order
- `get_open_orders`: Get open orders

### Market Data

- `get_market_data`: Get real-time market data
- `get_historical_data`: Get historical data

### Connection Management

- `connection_status`: Check connection status
- `reconnect`: Reconnect to IBKR

## Usage Examples

### Place Order

```json
{
    "tool": "place_order",
    "arguments": {
        "contract": {
            "symbol": "AAPL",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD"
        },
        "order": {
            "action": "BUY",
            "total_quantity": 100,
            "order_type": "LMT",
            "lmt_price": 150.0
        }
    }
}
```

### Get Positions

```json
{
    "tool": "get_positions",
    "arguments": {}
}
```

### Get Historical Data

```json
{
    "tool": "get_historical_data",
    "arguments": {
        "contract": {
            "symbol": "AAPL",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD"
        },
        "duration": "1 D",
        "bar_size": "1 min"
    }
}
```

## Architecture

```
┌─────────────────────┐
│   MCP Client        │
│ (Claude Desktop,    │
│  Custom Client)     │
└─────────┬───────────┘
          │ HTTP/WebSocket
┌─────────┴───────────┐
│   FastMCP Server    │
│ (MCP Protocol Layer)│
├─────────────────────┤
│   IBKR MCP Server   │
│ (Business Logic)    │
├─────────────────────┤
│   IBKR Client       │
│ (API Wrapper)       │
└─────────┬───────────┘
          │ TWS API
┌─────────┴───────────┐
│   TWS/Gateway       │
│ (IBKR Platform)     │
└─────────────────────┘
```

## Development

### Project Structure

```
src/ibkr_mcp_server/
├── __init__.py          # Package initialization
├── server.py            # MCP server implementation
├── client.py            # IBKR client wrapper
├── models.py            # Data models
├── config.py            # Configuration management
├── exceptions.py        # Exception definitions
└── cli.py              # Command line interface
```

### Code Standards

- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for code linting
- Use `mypy` for type checking

### Testing

```bash
# Run tests
pytest

# Generate coverage report
pytest --cov=src --cov-report=html
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t ibkr-mcp-server .

# Run container
docker run -p 8080:8080 --env-file .env ibkr-mcp-server
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Integration with Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "ibkr": {
      "command": "python",
      "args": ["-m", "ibkr_mcp_server.cli", "serve"],
      "env": {
        "IBKR__HOST": "127.0.0.1",
        "IBKR__PORT": "4002",
        "IBKR__CLIENT_ID": "1"
      }
    }
  }
}
```

## Important Notes

1. **TWS/Gateway**: Ensure IBKR TWS or Gateway is running with API connection enabled
2. **Port Configuration**: Make sure TWS/Gateway API port matches your configuration
3. **Permissions**: Ensure your account has appropriate trading permissions
4. **Risk Management**: Please implement proper risk controls in production environments
5. **Market Data**: Some market data may require subscriptions

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check if TWS/Gateway is running and API is enabled
2. **Client ID Conflict**: Use different client IDs for multiple connections
3. **Port Issues**: Verify the correct port for your TWS/Gateway setup
4. **Market Data Errors**: Ensure you have proper market data subscriptions

### Logging

Enable debug logging for troubleshooting:

```bash
LOGGING__LEVEL=DEBUG python -m ibkr_mcp_server.cli serve
```

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues, please file an [Issue](https://github.com/yourusername/ibkr-mcp-server/issues).

---

**中文文档**: [README_zh_CN.md](README_zh_CN.md) 