"""
Custom exceptions for IBKR MCP Server.
"""


class IBKRMCPError(Exception):
    """Base exception for IBKR MCP Server."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConnectionError(IBKRMCPError):
    """Connection-related errors."""
    pass


class AuthenticationError(IBKRMCPError):
    """Authentication-related errors."""
    pass


class OrderError(IBKRMCPError):
    """Order-related errors."""
    pass


class MarketDataError(IBKRMCPError):
    """Market data-related errors."""
    pass


class ConfigurationError(IBKRMCPError):
    """Configuration-related errors."""
    pass


class ValidationError(IBKRMCPError):
    """Data validation errors."""
    pass


class TimeoutError(IBKRMCPError):
    """Timeout errors."""
    pass


class RateLimitError(IBKRMCPError):
    """Rate limiting errors."""
    pass 