"""
Basic usage example for IBKR MCP Server.
"""

import asyncio
from ibkr_mcp_server import IBKRMCPServer, ServerConfig


async def main():
    """Main example function."""
    
    # Create configuration
    config = ServerConfig.from_env()
    
    # Override some settings for example
    config.ibkr.host = "127.0.0.1"
    config.ibkr.port = 4002
    config.ibkr.readonly = True  # Use read-only mode for safety
    config.mcp.port = 8080
    
    # Create and start server
    server = IBKRMCPServer(config)
    
    try:
        print("Starting IBKR MCP Server...")
        await server.start()
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main()) 