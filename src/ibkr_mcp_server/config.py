"""
Configuration management for IBKR MCP Server.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class IBKRConfig(BaseModel):
    """Interactive Brokers connection configuration."""
    
    host: str = Field(default="127.0.0.1", description="TWS/Gateway host")
    port: int = Field(default=7497, description="TWS/Gateway port")
    client_id: int = Field(default=1, description="Client ID for connection")
    readonly: bool = Field(default=False, description="Read-only mode")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @field_validator('client_id')
    @classmethod
    def validate_client_id(cls, v):
        if not 0 <= v <= 32:
            raise ValueError('Client ID must be between 0 and 32')
        return v


class MCPConfig(BaseModel):
    """MCP server configuration."""
    
    host: str = Field(default="0.0.0.0", description="MCP server host")
    port: int = Field(default=8080, description="MCP server port")
    max_connections: int = Field(default=100, description="Maximum concurrent connections")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}",
        description="Log format"
    )
    rotation: str = Field(default="1 day", description="Log rotation")
    retention: str = Field(default="30 days", description="Log retention")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = {'TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Level must be one of {valid_levels}')
        return v.upper()


class ServerConfig(BaseSettings):
    """Main server configuration."""
    
    ibkr: IBKRConfig = Field(default_factory=IBKRConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Environment-specific settings
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables and .env file."""
        return cls()
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production" 