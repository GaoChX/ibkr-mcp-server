"""
IBKR Client wrapper for async operations.
"""

import asyncio
import logging
import decimal
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from ib_insync import IB, Contract as IBContract, Order as IBOrder, Trade, Position as IBPosition
from ib_insync import Stock, Option, Future, Forex, Index, CFD
from loguru import logger

from .config import IBKRConfig
from .models import (
    Contract, Order, Position, AccountSummary, AccountValue,
    TickData, BarData, OrderExecution, MCPResponse,
    SecType, OrderAction, OrderType, TimeInForce
)
from .exceptions import ConnectionError, OrderError, MarketDataError, TimeoutError

logger = logging.getLogger(__name__)

class IBKRClient:
    """Async wrapper for Interactive Brokers API."""
    
    def __init__(self, config: IBKRConfig):
        self.config = config
        self.ib = IB()
        self._connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
    
    async def connect(self) -> bool:
        """Connect to IBKR TWS/Gateway."""
        try:
            logger.info(f"Connecting to IBKR at {self.config.host}:{self.config.port}")
            
            await self.ib.connectAsync(
                host=self.config.host,
                port=self.config.port,
                clientId=self.config.client_id,
                timeout=self.config.timeout,
                readonly=self.config.readonly
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            
            logger.info("Successfully connected to IBKR")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise ConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from IBKR")
    
    def is_connected(self) -> bool:
        """Check if connected to IBKR."""
        return self._connected and self.ib.isConnected()
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to IBKR."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            raise ConnectionError("Maximum reconnection attempts exceeded")
        
        self._reconnect_attempts += 1
        logger.warning(f"Attempting reconnection ({self._reconnect_attempts}/{self._max_reconnect_attempts})")
        
        try:
            await self.disconnect()
            await asyncio.sleep(2)  # Wait before reconnecting
            return await self.connect()
        except Exception as e:
            logger.error(f"Reconnection attempt {self._reconnect_attempts} failed: {e}")
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                raise ConnectionError(f"All reconnection attempts failed: {e}")
            return False
    
    def _ensure_connected(self) -> None:
        """Ensure connection is active."""
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")
    
    def _contract_to_ib(self, contract: Contract) -> IBContract:
        """Convert internal Contract to IB Contract."""
        if contract.sec_type == SecType.STOCK:
            return Stock(
                symbol=contract.symbol,
                exchange=contract.exchange,
                currency=contract.currency
            )
        elif contract.sec_type == SecType.OPTION:
            return Option(
                symbol=contract.symbol,
                lastTradeDateOrContractMonth=contract.expiry or '',
                strike=float(contract.strike or 0),
                right=contract.right or 'C',
                exchange=contract.exchange,
                currency=contract.currency
            )
        elif contract.sec_type == SecType.FUTURE:
            return Future(
                symbol=contract.symbol,
                lastTradeDateOrContractMonth=contract.last_trade_date or '',
                exchange=contract.exchange,
                currency=contract.currency
            )
        elif contract.sec_type == SecType.FOREX:
            return Forex(
                pair=contract.symbol,
                exchange=contract.exchange,
                currency=contract.currency
            )
        else:
            # Fallback to generic contract
            ib_contract = IBContract()
            ib_contract.symbol = contract.symbol
            ib_contract.secType = contract.sec_type.value
            ib_contract.exchange = contract.exchange
            ib_contract.currency = contract.currency
            if contract.local_symbol:
                ib_contract.localSymbol = contract.local_symbol
            return ib_contract
    
    def _order_to_ib(self, order: Order) -> IBOrder:
        """Convert internal Order to IB Order."""
        ib_order = IBOrder()
        ib_order.orderId = order.order_id or 0
        ib_order.clientId = order.client_id or self.config.client_id
        ib_order.action = order.action.value
        ib_order.totalQuantity = float(order.total_quantity)
        ib_order.orderType = order.order_type.value
        ib_order.tif = order.time_in_force.value
        ib_order.outsideRth = order.outside_rth
        ib_order.hidden = order.hidden
        
        if order.lmt_price:
            ib_order.lmtPrice = float(order.lmt_price)
        if order.aux_price:
            ib_order.auxPrice = float(order.aux_price)
        if order.good_after_time:
            ib_order.goodAfterTime = order.good_after_time
        if order.good_till_date:
            ib_order.goodTillDate = order.good_till_date
        
        return ib_order
    
    async def get_account_summary(self, tags: str = "All") -> List[AccountSummary]:
        """Get account summary information."""
        self._ensure_connected()
        
        try:
            import nest_asyncio
            nest_asyncio.apply()
            
            summary_items = self.ib.accountSummary()
            
            if not summary_items:
                self.ib.reqAccountUpdates(True)
                await asyncio.sleep(2)  # 等待更长时间
                summary_items = self.ib.accountSummary()
            
            return [
                AccountSummary(
                    account=item.account,
                    tag=item.tag,
                    value=item.value,
                    currency=item.currency
                )
                for item in summary_items
            ]
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            try:
                account_values = self.ib.accountValues()
                result = []
                for item in account_values[:10]:  
                    result.append(AccountSummary(
                        account=item.account,
                        tag=item.tag,
                        value=item.value,
                        currency=item.currency
                    ))
                return result
            except:
                raise MarketDataError(f"Account summary error: {e}")
    
    async def get_account_values(self) -> List[AccountValue]:
        """Get account values."""
        self._ensure_connected()
        
        try:
            account_values = await self.ib.reqAccountUpdatesAsync()
            return [
                AccountValue(
                    account=item.account,
                    key=item.tag,
                    value=item.value,
                    currency=item.currency
                )
                for item in account_values
            ]
        except Exception as e:
            logger.error(f"Failed to get account values: {e}")
            raise MarketDataError(f"Account values error: {e}")
    
    async def get_positions(self) -> List[Position]:
        """Get all positions."""
        self._ensure_connected()
        
        try:
            positions = await self.ib.reqPositionsAsync()
            result = []
            
            for pos in positions:
                contract = Contract(
                    symbol=pos.contract.symbol,
                    sec_type=SecType(pos.contract.secType),
                    exchange=pos.contract.exchange,
                    currency=pos.contract.currency
                )
                
                position = Position(
                    account=pos.account,
                    contract=contract,
                    position=Decimal(str(pos.position)),
                    avg_cost=Decimal(str(pos.avgCost))
                )
                result.append(position)
            
            return result
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise MarketDataError(f"Positions error: {e}")
    
    async def place_order(self, contract: Contract, order: Order) -> Trade:
        """Place an order."""
        self._ensure_connected()
        
        try:
            ib_contract = self._contract_to_ib(contract)
            ib_order = self._order_to_ib(order)
            
            # Qualify contract if needed
            qualified_contracts = await self.ib.qualifyContractsAsync(ib_contract)
            if not qualified_contracts:
                raise OrderError(f"Could not qualify contract: {contract.symbol}")
            
            ib_contract = qualified_contracts[0]
            
            # Place order
            trade = self.ib.placeOrder(ib_contract, ib_order)
            
            logger.info(f"Order placed: {trade.order.orderId} for {contract.symbol}")
            return trade
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise OrderError(f"Order placement error: {e}")
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an order."""
        self._ensure_connected()
        
        try:
            # 首先获取所有开放的交易来找到对应的订单
            open_trades = self.ib.openTrades()
            
            # 查找匹配的订单
            target_order = None
            for trade in open_trades:
                if trade.order.orderId == order_id:
                    target_order = trade.order
                    break
            
            if target_order is None:
                logger.error(f"Order with ID {order_id} not found in open trades")
                raise OrderError(f"Order {order_id} not found")
            
            # 使用找到的Order对象来取消订单
            self.ib.cancelOrder(target_order)
            logger.info(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise OrderError(f"Order cancellation error: {e}")
    
    async def get_open_orders(self) -> List[Trade]:
        """Get all open orders."""
        self._ensure_connected()
        
        try:
            await self.ib.reqOpenOrdersAsync()
            return self.ib.openTrades()
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise OrderError(f"Open orders error: {e}")
    
    async def get_historical_data(
        self,
        contract: Contract,
        duration: str = "1 D",
        bar_size: str = "1 min",
        what_to_show: str = "TRADES",
        use_rth: bool = True
    ) -> List[BarData]:
        """Get historical market data."""
        self._ensure_connected()
        
        try:
            ib_contract = self._contract_to_ib(contract)
            
            # Qualify contract
            qualified_contracts = await self.ib.qualifyContractsAsync(ib_contract)
            if not qualified_contracts:
                raise MarketDataError(f"Could not qualify contract: {contract.symbol}")
            
            ib_contract = qualified_contracts[0]
            
            # Request historical data
            bars = await self.ib.reqHistoricalDataAsync(
                contract=ib_contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth
            )
            
            return [
                BarData(
                    date=bar.date,
                    open=Decimal(str(bar.open)),
                    high=Decimal(str(bar.high)),
                    low=Decimal(str(bar.low)),
                    close=Decimal(str(bar.close)),
                    volume=bar.volume,
                    wap=Decimal(str(bar.wap)) if bar.wap else None,
                    count=bar.count if hasattr(bar, 'count') else None
                )
                for bar in bars
            ]
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            raise MarketDataError(f"Historical data error: {e}")
    
    async def get_market_data(self, contract: Contract) -> Optional[TickData]:
        """Get real-time market data."""
        self._ensure_connected()
        
        try:
            ib_contract = self._contract_to_ib(contract)
            
            # Qualify contract
            qualified_contracts = await self.ib.qualifyContractsAsync(ib_contract)
            if not qualified_contracts:
                raise MarketDataError(f"Could not qualify contract: {contract.symbol}")
            
            ib_contract = qualified_contracts[0]
            
            # Request market data snapshot
            ticker = self.ib.reqMktData(ib_contract, '', True, False)
            
            # Wait for data to be populated
            await asyncio.sleep(0.5)
            
            if ticker and ticker.last:
                # 安全地处理价格和大小数据
                price = None
                size = None
                
                # 检查价格是否有效
                if ticker.last and str(ticker.last).lower() not in ['nan', 'inf', '-inf']:
                    try:
                        price_val = Decimal(str(ticker.last))
                        if price_val.is_finite():
                            price = price_val
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        price = None
                
                # 检查大小是否有效
                if hasattr(ticker, 'lastSize') and ticker.lastSize is not None:
                    try:
                        size_val = float(ticker.lastSize)
                        if size_val == size_val and size_val != float('inf') and size_val != float('-inf') and size_val >= 0:
                            size = int(size_val)
                    except (ValueError, TypeError):
                        size = None
                
                return TickData(
                    symbol=contract.symbol,
                    tick_type=1,  # Last price
                    price=price,
                    size=size
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            raise MarketDataError(f"Market data error: {e}")
    
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator['IBKRClient', None]:
        """Context manager for IBKR connection."""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect() 