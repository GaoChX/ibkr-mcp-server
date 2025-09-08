"""
Command line interface for IBKR MCP Server.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from loguru import logger

from .config import ServerConfig
from .server import IBKRMCPServer
from .exceptions import IBKRMCPError


app = typer.Typer(
    name="ibkr-mcp-server",
    help="Interactive Brokers MCP Server",
    add_completion=False
)
console = Console()


def setup_logging(config: ServerConfig) -> None:
    """Setup logging configuration."""
    logger.remove()  # Remove default handler
    
    logger.add(
        sys.stderr,
        level=config.logging.level,
        format=config.logging.format,
    )
    
    if not config.is_production():
        logger.add(
            "logs/ibkr-mcp-server.log",
            level=config.logging.level,
            format=config.logging.format,
            rotation=config.logging.rotation,
            retention=config.logging.retention,
            compression="zip"
        )


@app.command()
def serve(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Configuration file path"
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        help="MCP server host"
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        help="MCP server port"
    ),
    ibkr_host: Optional[str] = typer.Option(
        None,
        "--ibkr-host",
        help="IBKR TWS/Gateway host"
    ),
    ibkr_port: Optional[int] = typer.Option(
        None,
        "--ibkr-port",
        help="IBKR TWS/Gateway port"
    ),
    client_id: Optional[int] = typer.Option(
        None,
        "--client-id",
        help="IBKR client ID"
    ),
    readonly: bool = typer.Option(
        False,
        "--readonly",
        help="Connect in read-only mode"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode"
    ),
) -> None:
    """Start the IBKR MCP Server."""
    
    try:
        # Load configuration
        config = ServerConfig.from_env()
        
        # Override with CLI arguments
        if host:
            config.mcp.host = host
        if port:
            config.mcp.port = port
        if ibkr_host:
            config.ibkr.host = ibkr_host
        if ibkr_port:
            config.ibkr.port = ibkr_port
        if client_id:
            config.ibkr.client_id = client_id
        if readonly:
            config.ibkr.readonly = readonly
        if debug:
            config.debug = debug
            config.logging.level = "DEBUG"
        
        # Setup logging
        setup_logging(config)
        
        # Display startup info
        console.print(Panel.fit(
            Text("IBKR MCP Server", style="bold blue"),
            title="Starting",
            border_style="blue"
        ))
        
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("MCP Host", config.mcp.host)
        table.add_row("MCP Port", str(config.mcp.port))
        table.add_row("IBKR Host", config.ibkr.host)
        table.add_row("IBKR Port", str(config.ibkr.port))
        table.add_row("Client ID", str(config.ibkr.client_id))
        table.add_row("Read-only", str(config.ibkr.readonly))
        table.add_row("Debug", str(config.debug))
        
        console.print(table)
        
        # Run server
        asyncio.run(run_server(config))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Server startup failed")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration"
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Initialize configuration file"
    ),
) -> None:
    """Configuration management."""
    
    if show:
        config = ServerConfig.from_env()
        
        console.print(Panel.fit(
            Text("IBKR MCP Server Configuration", style="bold blue"),
            border_style="blue"
        ))
        
        console.print(f"[cyan]Configuration:[/cyan]\n{config.json(indent=2)}")
    
    elif init:
        env_content = """# IBKR MCP Server Configuration

# MCP Server Settings
MCP__HOST=0.0.0.0
MCP__PORT=8080
MCP__MAX_CONNECTIONS=100
MCP__REQUEST_TIMEOUT=30

# IBKR Connection Settings
IBKR__HOST=127.0.0.1
IBKR__PORT=4002
IBKR__CLIENT_ID=1
IBKR__READONLY=false
IBKR__TIMEOUT=30

# Logging Settings
LOGGING__LEVEL=INFO
LOGGING__ROTATION=1 day
LOGGING__RETENTION=30 days

# Environment
ENVIRONMENT=development
DEBUG=false
"""
        
        env_file = Path(".env")
        if env_file.exists():
            if not typer.confirm("Configuration file already exists. Overwrite?"):
                return
        
        env_file.write_text(env_content)
        console.print(f"[green]Configuration file created: {env_file}[/green]")
    
    else:
        console.print("[yellow]Use --show to display configuration or --init to create .env file[/yellow]")


@app.command()
def test(
    host: str = typer.Option("127.0.0.1", help="IBKR host"),
    port: int = typer.Option(4002, help="IBKR port"),
    client_id: int = typer.Option(1, help="Client ID"),
    timeout: int = typer.Option(10, help="Connection timeout"),
) -> None:
    """Test IBKR connection."""
    
    console.print(Panel.fit(
        Text("Testing IBKR Connection", style="bold blue"),
        border_style="blue"
    ))
    
    asyncio.run(test_connection(host, port, client_id, timeout))


async def run_server(config: ServerConfig) -> None:
    """Run the MCP server."""
    server = IBKRMCPServer(config)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.stop()


async def test_connection(host: str, port: int, client_id: int, timeout: int) -> None:
    """Test IBKR connection."""
    from .client import IBKRClient
    from .config import IBKRConfig
    
    config = IBKRConfig(
        host=host,
        port=port,
        client_id=client_id,
        timeout=timeout
    )
    
    client = IBKRClient(config)
    
    try:
        console.print(f"[yellow]Connecting to {host}:{port}...[/yellow]")
        
        success = await client.connect()
        
        if success:
            console.print("[green]✓ Connection successful![/green]")
            
            # Test basic functionality
            try:
                accounts = await client.get_account_summary()
                console.print(f"[green]✓ Account access: {len(accounts)} items[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Account access limited: {e}[/yellow]")
            
        else:
            console.print("[red]✗ Connection failed[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Connection error: {e}[/red]")
    finally:
        await client.disconnect()


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main() 