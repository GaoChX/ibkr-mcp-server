"""
Pydantic models for IBKR MCP Server data structures.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class OrderAction(str, Enum):
    """Order action types."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP LMT"
    TRAIL = "TRAIL"
    TRAIL_LIMIT = "TRAIL LIMIT"


class OrderStatus(str, Enum):
    """Order status types."""
    PENDING_SUBMIT = "PendingSubmit"
    PENDING_CANCEL = "PendingCancel"
    PRE_SUBMITTED = "PreSubmitted"
    SUBMITTED = "Submitted"
    CANCELLED = "Cancelled"
    FILLED = "Filled"
    INACTIVE = "Inactive"
    PENDING_REJECT = "PendingReject"
    REJECTED = "Rejected"


class TimeInForce(str, Enum):
    """Time in force types."""
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    GTD = "GTD"


class SecType(str, Enum):
    """Security types."""
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    FOREX = "CASH"
    INDEX = "IND"
    CFD = "CFD"
    BOND = "BOND"
    WARRANT = "WAR"
    COMMODITY = "CMDTY"


class Contract(BaseModel):
    """Contract information."""
    
    symbol: str = Field(..., description="Contract symbol")
    sec_type: SecType = Field(..., description="Security type")
    exchange: str = Field(default="SMART", description="Exchange")
    currency: str = Field(default="USD", description="Currency")
    local_symbol: Optional[str] = Field(None, description="Local symbol")
    con_id: Optional[int] = Field(None, description="Contract ID")
    
    # Options specific
    strike: Optional[Decimal] = Field(None, description="Strike price for options")
    right: Optional[str] = Field(None, description="Right (C/P) for options")
    expiry: Optional[str] = Field(None, description="Expiry date")
    
    # Futures specific
    last_trade_date: Optional[str] = Field(None, description="Last trade date for futures")
    multiplier: Optional[int] = Field(None, description="Contract multiplier")


class Order(BaseModel):
    """Order information."""
    
    order_id: Optional[int] = Field(None, description="Order ID")
    client_id: Optional[int] = Field(None, description="Client ID")
    action: OrderAction = Field(..., description="Order action (BUY/SELL)")
    total_quantity: Decimal = Field(..., description="Total quantity")
    order_type: OrderType = Field(..., description="Order type")
    lmt_price: Optional[Decimal] = Field(None, description="Limit price")
    aux_price: Optional[Decimal] = Field(None, description="Auxiliary price (stop price)")
    time_in_force: TimeInForce = Field(default=TimeInForce.DAY, description="Time in force")
    
    # Optional parameters
    good_after_time: Optional[str] = Field(None, description="Good after time")
    good_till_date: Optional[str] = Field(None, description="Good till date")
    outside_rth: bool = Field(default=False, description="Allow outside regular trading hours")
    hidden: bool = Field(default=False, description="Hidden order")
    
    @field_validator('total_quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class OrderExecution(BaseModel):
    """Order execution information."""
    
    exec_id: str = Field(..., description="Execution ID")
    order_id: int = Field(..., description="Order ID")
    symbol: str = Field(..., description="Symbol")
    side: str = Field(..., description="Side (BOT/SLD)")
    shares: Decimal = Field(..., description="Executed shares")
    price: Decimal = Field(..., description="Execution price")
    cum_qty: Decimal = Field(..., description="Cumulative quantity")
    avg_price: Decimal = Field(..., description="Average price")
    time: datetime = Field(..., description="Execution time")


class Position(BaseModel):
    """Position information."""
    
    account: str = Field(..., description="Account")
    contract: Contract = Field(..., description="Contract")
    position: Decimal = Field(..., description="Position size")
    avg_cost: Decimal = Field(..., description="Average cost")
    market_price: Optional[Decimal] = Field(None, description="Current market price")
    market_value: Optional[Decimal] = Field(None, description="Market value")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Unrealized P&L")
    realized_pnl: Optional[Decimal] = Field(None, description="Realized P&L")


class AccountSummary(BaseModel):
    """Account summary information."""
    
    account: str = Field(..., description="Account ID")
    tag: str = Field(..., description="Summary tag")
    value: str = Field(..., description="Summary value")
    currency: str = Field(..., description="Currency")


class AccountValue(BaseModel):
    """Account value information."""
    
    account: str = Field(..., description="Account")
    key: str = Field(..., description="Value key")
    value: str = Field(..., description="Value")
    currency: str = Field(..., description="Currency")


class TickData(BaseModel):
    """Market tick data."""
    
    symbol: str = Field(..., description="Symbol")
    tick_type: int = Field(..., description="Tick type")
    price: Optional[Decimal] = Field(None, description="Price")
    size: Optional[int] = Field(None, description="Size")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is None:
            return None
        # 检查是否为NaN
        if isinstance(v, Decimal) and not v.is_finite():
            return None
        if isinstance(v, (int, float)) and (v != v or v == float('inf') or v == float('-inf')):  # NaN check
            return None
        return v
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        if v is None:
            return None
        # 检查是否为NaN或无穷大
        if isinstance(v, (int, float)) and (v != v or v == float('inf') or v == float('-inf')):  # NaN check
            return None
        if v < 0:  # 负数大小无效
            return None
        return v


class BarData(BaseModel):
    """Historical bar data."""
    
    date: datetime = Field(..., description="Bar date/time")
    open: Decimal = Field(..., description="Open price")
    high: Decimal = Field(..., description="High price")
    low: Decimal = Field(..., description="Low price")
    close: Decimal = Field(..., description="Close price")
    volume: int = Field(..., description="Volume")
    wap: Optional[Decimal] = Field(None, description="Weighted average price")
    count: Optional[int] = Field(None, description="Trade count")


class MarketDataRequest(BaseModel):
    """Market data request."""
    
    contract: Contract = Field(..., description="Contract to request data for")
    what_to_show: str = Field(default="TRADES", description="What to show")
    bar_size: str = Field(default="1 min", description="Bar size")
    duration: str = Field(default="1 D", description="Duration")
    use_rth: bool = Field(default=True, description="Use regular trading hours")


class OrderRequest(BaseModel):
    """Order placement request."""
    
    contract: Contract = Field(..., description="Contract to trade")
    order: Order = Field(..., description="Order details")


class MCPResponse(BaseModel):
    """Generic MCP response wrapper."""
    
    success: bool = Field(..., description="Success status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp") 