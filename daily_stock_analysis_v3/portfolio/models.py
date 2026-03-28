"""
Portfolio Data Models

Core models for portfolio, positions, trades, and cash flows.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Trade types"""
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    """Trade status"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """
    Trade record.
    
    Represents a single buy or sell transaction.
    """
    id: str
    portfolio_id: str
    stock_code: str
    stock_name: str
    trade_type: TradeType
    quantity: float
    price: float
    commission: float = 0.0
    currency: str = "USD"
    trade_date: date = field(default_factory=date.today)
    settle_date: Optional[date] = None
    status: TradeStatus = TradeStatus.PENDING
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_value(self) -> float:
        """Calculate total trade value including commission"""
        base_value = self.quantity * self.price
        if self.trade_type == TradeType.BUY:
            return base_value + self.commission
        else:
            return base_value - self.commission
    
    @property
    def executed(self) -> bool:
        """Check if trade is executed"""
        return self.status == TradeStatus.EXECUTED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'trade_type': self.trade_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'currency': self.currency,
            'trade_date': self.trade_date.isoformat(),
            'settle_date': self.settle_date.isoformat() if self.settle_date else None,
            'status': self.status.value,
            'notes': self.notes,
            'total_value': self.total_value,
            'created_at': self.created_at.isoformat(),
        }
    
    def execute(self) -> None:
        """Mark trade as executed"""
        self.status = TradeStatus.EXECUTED
        self.settle_date = self.trade_date
        logger.info(f"Trade executed: {self.id}")
    
    def cancel(self) -> None:
        """Cancel trade"""
        self.status = TradeStatus.CANCELLED
        logger.info(f"Trade cancelled: {self.id}")


@dataclass
class Position:
    """
    Stock position.
    
    Represents holdings in a single stock.
    """
    id: str
    portfolio_id: str
    stock_code: str
    stock_name: str
    quantity: float = 0.0
    average_cost: float = 0.0
    current_price: float = 0.0
    currency: str = "USD"
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Calculate current market value"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Calculate total cost basis"""
        return self.quantity * self.average_cost
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss"""
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    @property
    def is_long(self) -> bool:
        """Check if long position"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if short position"""
        return self.quantity < 0
    
    def update_price(self, price: float) -> None:
        """Update current price"""
        self.current_price = price
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'quantity': self.quantity,
            'average_cost': self.average_cost,
            'current_price': self.current_price,
            'currency': self.currency,
            'market_value': self.market_value,
            'cost_basis': self.cost_basis,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'last_updated': self.last_updated.isoformat(),
        }


@dataclass
class CashFlow:
    """
    Cash flow record.
    
    Represents deposits, withdrawals, dividends, etc.
    """
    id: str
    portfolio_id: str
    flow_type: str  # deposit, withdrawal, dividend, interest, fee
    amount: float
    currency: str = "USD"
    flow_date: date = field(default_factory=date.today)
    description: str = ""
    reference: str = ""  # Reference ID (e.g., dividend payment ID)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_inflow(self) -> bool:
        """Check if cash inflow"""
        return self.flow_type in ['deposit', 'dividend', 'interest']
    
    @property
    def is_outflow(self) -> bool:
        """Check if cash outflow"""
        return self.flow_type in ['withdrawal', 'fee']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'flow_type': self.flow_type,
            'amount': self.amount,
            'currency': self.currency,
            'flow_date': self.flow_date.isoformat(),
            'description': self.description,
            'reference': self.reference,
            'is_inflow': self.is_inflow,
            'is_outflow': self.is_outflow,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class Portfolio:
    """
    Portfolio container.
    
    Holds positions, trades, and cash flows for a single portfolio.
    """
    id: str
    name: str
    base_currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.now)
    
    # Holdings
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    cash_flows: List[CashFlow] = field(default_factory=list)
    
    # Cash
    cash_balance: float = 0.0
    
    @property
    def total_market_value(self) -> float:
        """Calculate total market value of positions"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_cost_basis(self) -> float:
        """Calculate total cost basis"""
        return sum(pos.cost_basis for pos in self.positions.values())
    
    @property
    def total_equity(self) -> float:
        """Calculate total equity (market value + cash)"""
        return self.total_market_value + self.cash_balance
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def total_return_percent(self) -> float:
        """Calculate total return percentage"""
        if self.total_cost_basis == 0:
            return 0.0
        return (self.total_unrealized_pnl / self.total_cost_basis) * 100
    
    @property
    def position_count(self) -> int:
        """Get number of positions"""
        return len([p for p in self.positions.values() if p.quantity != 0])
    
    def add_position(self, position: Position) -> None:
        """Add or update position"""
        self.positions[position.stock_code] = position
        logger.info(f"Position added: {position.stock_code}")
    
    def add_trade(self, trade: Trade) -> None:
        """Add trade and update position"""
        self.trades.append(trade)
        
        # Update position
        if trade.stock_code not in self.positions:
            self.positions[trade.stock_code] = Position(
                id=f"pos_{trade.stock_code}",
                portfolio_id=self.id,
                stock_code=trade.stock_code,
                stock_name=trade.stock_name,
                currency=trade.currency,
            )
        
        position = self.positions[trade.stock_code]
        
        if trade.executed:
            if trade.trade_type == TradeType.BUY:
                # Update average cost
                total_cost = (position.quantity * position.average_cost) + trade.total_value
                position.quantity += trade.quantity
                if position.quantity > 0:
                    position.average_cost = total_cost / position.quantity
            else:  # SELL
                position.quantity -= trade.quantity
                if position.quantity < 0:
                    position.quantity = 0
                    position.average_cost = 0
            
            # Update cash
            if trade.trade_type == TradeType.BUY:
                self.cash_balance -= trade.total_value
            else:
                self.cash_balance += trade.total_value
        
        logger.info(f"Trade added: {trade.id}")
    
    def add_cash_flow(self, cash_flow: CashFlow) -> None:
        """Add cash flow"""
        self.cash_flows.append(cash_flow)
        
        # Update cash balance
        if cash_flow.is_inflow:
            self.cash_balance += cash_flow.amount
        elif cash_flow.is_outflow:
            self.cash_balance -= cash_flow.amount
        
        logger.info(f"Cash flow added: {cash_flow.id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'base_currency': self.base_currency,
            'cash_balance': self.cash_balance,
            'total_market_value': self.total_market_value,
            'total_cost_basis': self.total_cost_basis,
            'total_equity': self.total_equity,
            'total_unrealized_pnl': self.total_unrealized_pnl,
            'total_return_percent': self.total_return_percent,
            'position_count': self.position_count,
            'positions': [p.to_dict() for p in self.positions.values()],
            'trade_count': len(self.trades),
            'cash_flow_count': len(self.cash_flows),
            'created_at': self.created_at.isoformat(),
        }
