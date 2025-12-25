#!/bin/bash

# Test MCP Protocol Endpoints
echo "Testing IBKR MCP Server Protocol Endpoints"
echo "==========================================="
echo ""

SERVER="http://localhost:8080"

# Test 1: Initialize
echo "1. Testing MCP Initialize..."
curl -s -X POST "$SERVER/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }' | jq '.'
echo ""

# Test 2: Initialized notification
echo "2. Testing MCP Initialized (notification)..."
curl -s -X POST "$SERVER/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialized"
  }'
echo ""
echo "✓ Initialized notification sent"
echo ""

# Test 3: List tools
echo "3. Testing tools/list..."
curl -s -X POST "$SERVER/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' | jq '.result.tools[] | {name, description}'
echo ""

# Test 4: Call a tool
echo "4. Testing tools/call (connection_status)..."
curl -s -X POST "$SERVER/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "connection_status",
      "arguments": {}
    }
  }' | jq '.'
echo ""

echo "==========================================="
echo "✓ All MCP protocol tests completed!"
