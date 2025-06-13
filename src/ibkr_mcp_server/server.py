"""
Main IBKR MCP Server implementation using fastmcp and streamablehttp.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolResult, ListToolsResult, Tool, TextContent,
    JSONRPCMessage, JSONRPCRequest, JSONRPCResponse
)
from loguru import logger

from .config import ServerConfig
from .client import IBKRClient
from .models import (
    Contract, Order, MCPResponse, OrderRequest, MarketDataRequest,
    SecType, OrderAction, OrderType, TimeInForce
)
from .exceptions import IBKRMCPError, ConnectionError, OrderError, MarketDataError


class IBKRMCPServer:
    """IBKR MCP Server implementation."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.ibkr_client = IBKRClient(config.ibkr)
        self.mcp = FastMCP("IBKR MCP Server")
        self._setup_tools()
    
    def _setup_tools(self) -> None:
        """Setup MCP tools."""
        
        # Account management tools
        @self.mcp.tool()
        async def get_account_summary(tags: str = "All") -> Dict[str, Any]:
            """Get account summary information."""
            try:
                summary = await self.ibkr_client.get_account_summary(tags)
                return {
                    "success": True,
                    "data": [item.dict() for item in summary],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Account summary error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def get_positions() -> Dict[str, Any]:
            """Get all positions."""
            try:
                positions = await self.ibkr_client.get_positions()
                return {
                    "success": True,
                    "data": [pos.dict() for pos in positions],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Positions error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Trading tools
        @self.mcp.tool()
        async def place_order(
            symbol: str,
            sec_type: str,
            action: str,
            quantity: float,
            order_type: str,
            exchange: str = "SMART",
            currency: str = "USD",
            limit_price: Optional[float] = None,
            stop_price: Optional[float] = None
        ) -> Dict[str, Any]:
            """Place a trading order."""
            try:
                contract = Contract(
                    symbol=symbol,
                    sec_type=SecType(sec_type),
                    exchange=exchange,
                    currency=currency
                )
                
                order = Order(
                    action=OrderAction(action),
                    total_quantity=quantity,
                    order_type=OrderType(order_type),
                    lmt_price=limit_price,
                    aux_price=stop_price
                )
                
                trade = await self.ibkr_client.place_order(contract, order)
                
                return {
                    "success": True,
                    "data": {
                        "order_id": trade.order.orderId,
                        "status": trade.orderStatus.status,
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Order placement error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def cancel_order(order_id: int) -> Dict[str, Any]:
            """Cancel an order by ID."""
            try:
                success = await self.ibkr_client.cancel_order(order_id)
                return {
                    "success": success,
                    "data": {"order_id": order_id, "cancelled": success},
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Order cancellation error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def get_open_orders() -> Dict[str, Any]:
            """Get all open orders."""
            try:
                trades = await self.ibkr_client.get_open_orders()
                orders_data = []
                
                for trade in trades:
                    orders_data.append({
                        "order_id": trade.order.orderId,
                        "symbol": trade.contract.symbol,
                        "action": trade.order.action,
                        "quantity": trade.order.totalQuantity,
                        "order_type": trade.order.orderType,
                        "status": trade.orderStatus.status,
                        "limit_price": trade.order.lmtPrice,
                        "filled": trade.orderStatus.filled,
                        "remaining": trade.orderStatus.remaining
                    })
                
                return {
                    "success": True,
                    "data": orders_data,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Open orders error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Market data tools
        @self.mcp.tool()
        async def get_market_data(
            symbol: str,
            sec_type: str = "STK",
            exchange: str = "SMART",
            currency: str = "USD"
        ) -> Dict[str, Any]:
            """Get real-time market data."""
            try:
                contract = Contract(
                    symbol=symbol,
                    sec_type=SecType(sec_type),
                    exchange=exchange,
                    currency=currency
                )
                
                tick_data = await self.ibkr_client.get_market_data(contract)
                
                return {
                    "success": True,
                    "data": tick_data.dict() if tick_data else None,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Market data error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def get_historical_data(
            symbol: str,
            sec_type: str = "STK",
            duration: str = "1 D",
            bar_size: str = "1 min",
            exchange: str = "SMART",
            currency: str = "USD",
            what_to_show: str = "TRADES"
        ) -> Dict[str, Any]:
            """Get historical market data."""
            try:
                contract = Contract(
                    symbol=symbol,
                    sec_type=SecType(sec_type),
                    exchange=exchange,
                    currency=currency
                )
                
                bars = await self.ibkr_client.get_historical_data(
                    contract=contract,
                    duration=duration,
                    bar_size=bar_size,
                    what_to_show=what_to_show
                )
                
                return {
                    "success": True,
                    "data": [bar.dict() for bar in bars],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Historical data error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Connection tools
        @self.mcp.tool()
        async def connection_status() -> Dict[str, Any]:
            """Check IBKR connection status."""
            try:
                connected = self.ibkr_client.is_connected()
                return {
                    "success": True,
                    "data": {
                        "connected": connected,
                        "host": self.config.ibkr.host,
                        "port": self.config.ibkr.port,
                        "client_id": self.config.ibkr.client_id
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Connection status error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def reconnect() -> Dict[str, Any]:
            """Reconnect to IBKR."""
            try:
                success = await self.ibkr_client.reconnect()
                return {
                    "success": success,
                    "data": {"reconnected": success},
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Reconnection error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def start(self) -> None:
        """Start the MCP server."""
        try:
            logger.info("Starting IBKR MCP Server...")
            
            # Try to connect to IBKR (optional)
            try:
                await self.ibkr_client.connect()
                logger.success("Connected to IBKR successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to IBKR: {e}")
                logger.info("MCP server will start without IBKR connection (tools will return errors)")
            
            # Start MCP server
            await self.mcp.run_async(
                transport="streamable-http",
                host=self.config.mcp.host,
                port=self.config.mcp.port
            )
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        logger.info("Stopping IBKR MCP Server...")
        
        try:
            await self.ibkr_client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting from IBKR: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop() 