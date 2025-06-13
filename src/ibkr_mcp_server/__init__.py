"""
IBKR MCP Server - Interactive Brokers MCP Server Implementation

A modern, type-safe MCP server for Interactive Brokers TWS/Gateway integration
providing account management, trading operations, and market data access.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .server import IBKRMCPServer
from .config import ServerConfig
from .models import *

__all__ = [
    "IBKRMCPServer",
    "ServerConfig",
    "__version__",
] 