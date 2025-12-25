#!/bin/bash
# Test all MCP tools

echo "Testing IBKR MCP Server Tools"
echo "=============================="
echo ""

# Test 1: Health Check
echo "1. Health Check"
curl -s http://localhost:8080/health | jq .
echo ""

# Test 2: Connection Status
echo "2. Connection Status"
curl -s http://localhost:8080/mcp/status | jq .
echo ""

# Test 3: Account Summary
echo "3. Account Summary"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_account_summary", "parameters": {}}' | jq .
echo ""

# Test 4: Get Positions
echo "4. Get Positions"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_positions", "parameters": {}}' | jq .
echo ""

# Test 5: Place Order
echo "5. Place Order (AAPL)"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "place_order",
    "parameters": {
      "symbol": "AAPL",
      "sec_type": "STK",
      "action": "BUY",
      "quantity": 100,
      "order_type": "LMT",
      "limit_price": 175.00
    }
  }' | jq .
echo ""

# Test 6: Get Open Orders
echo "6. Get Open Orders"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_open_orders", "parameters": {}}' | jq .
echo ""

# Test 7: Get Market Data
echo "7. Get Market Data (MSFT)"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_market_data", "parameters": {"symbol": "MSFT"}}' | jq .
echo ""

# Test 8: Get Historical Data
echo "8. Get Historical Data (TSLA)"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_historical_data",
    "parameters": {
      "symbol": "TSLA",
      "duration": "1 D",
      "bar_size": "1 min"
    }
  }' | jq .
echo ""

# Test 9: Cancel Order
echo "9. Cancel Order"
curl -s -X POST http://localhost:8080/mcp/tools \
  -H "Content-Type: application/json" \
  -d '{"tool": "cancel_order", "parameters": {"order_id": 1001}}' | jq .
echo ""

echo "Testing complete!"
