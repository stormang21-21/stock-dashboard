"""
Portfolio Management System

Manage stock portfolios with real-time tracking.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Stock position in portfolio"""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float = 0.0
    company_name: str = ''
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.average_cost
    
    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_percent(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_cost': round(self.average_cost, 2),
            'current_price': round(self.current_price, 2),
            'company_name': self.company_name,
            'market_value': round(self.market_value, 2),
            'cost_basis': round(self.cost_basis, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'unrealized_pnl_percent': round(self.unrealized_pnl_percent, 2),
        }


@dataclass
class Transaction:
    """Buy/sell transaction"""
    id: str
    symbol: str
    type: str  # 'buy' or 'sell'
    quantity: float
    price: float
    total: float
    timestamp: str
    notes: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PortfolioManager:
    """Manage user portfolios"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.portfolios: Dict[str, Dict[str, Position]] = {}
        self.transactions: Dict[str, List[Transaction]] = {}
        self.cash: Dict[str, float] = {}
    
    def create_portfolio(self, user_id: str, initial_cash: float = 100000.0) -> bool:
        """Create a new portfolio for user"""
        if user_id not in self.portfolios:
            self.portfolios[user_id] = {}
            self.transactions[user_id] = []
            self.cash[user_id] = initial_cash
            logger.info(f"Created portfolio for {user_id} with ${initial_cash}")
            return True
        return False
    
    def add_position(self, user_id: str, symbol: str, quantity: float, price: float, company_name: str = '') -> bool:
        """Add or update a position (buy)"""
        if user_id not in self.portfolios:
            self.create_portfolio(user_id)
        
        total_cost = quantity * price
        
        # Check if sufficient cash
        if self.cash.get(user_id, 0) < total_cost:
            logger.error(f"Insufficient cash for {user_id}")
            return False
        
        # Deduct cash
        self.cash[user_id] -= total_cost
        
        # Update or create position
        if symbol in self.portfolios[user_id]:
            position = self.portfolios[user_id][symbol]
            # Calculate new average cost
            total_shares = position.quantity + quantity
            total_value = position.cost_basis + total_cost
            position.quantity = total_shares
            position.average_cost = total_value / total_shares if total_shares > 0 else 0
        else:
            self.portfolios[user_id][symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_cost=price,
                current_price=price,
                company_name=company_name
            )
        
        # Record transaction
        self.transactions[user_id].append(Transaction(
            id=f"txn_{datetime.now().timestamp()}",
            symbol=symbol,
            type='buy',
            quantity=quantity,
            price=price,
            total=total_cost,
            timestamp=datetime.now().isoformat(),
            notes=f'Bought {quantity} shares @ ${price}'
        ))
        
        logger.info(f"{user_id} bought {quantity} {symbol} @ ${price}")
        return True
    
    def remove_position(self, user_id: str, symbol: str, quantity: float, price: float) -> bool:
        """Remove or reduce a position (sell)"""
        if user_id not in self.portfolios:
            return False
        
        if symbol not in self.portfolios[user_id]:
            return False
        
        position = self.portfolios[user_id][symbol]
        
        if position.quantity < quantity:
            logger.error(f"Insufficient shares for {user_id}")
            return False
        
        # Add cash
        total_value = quantity * price
        self.cash[user_id] += total_value
        
        # Update or remove position
        position.quantity -= quantity
        if position.quantity <= 0:
            del self.portfolios[user_id][symbol]
        
        # Record transaction
        self.transactions[user_id].append(Transaction(
            id=f"txn_{datetime.now().timestamp()}",
            symbol=symbol,
            type='sell',
            quantity=quantity,
            price=price,
            total=total_value,
            timestamp=datetime.now().isoformat(),
            notes=f'Sold {quantity} shares @ ${price}'
        ))
        
        logger.info(f"{user_id} sold {quantity} {symbol} @ ${price}")
        return True
    
    def update_prices(self, user_id: str, prices: Dict[str, float]) -> None:
        """Update current prices for all positions"""
        if user_id not in self.portfolios:
            return
        
        for symbol, position in self.portfolios[user_id].items():
            if symbol in prices:
                position.current_price = prices[symbol]
    
    def get_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio summary"""
        if user_id not in self.portfolios:
            return {'error': 'Portfolio not found'}
        
        positions = self.portfolios[user_id]
        cash = self.cash.get(user_id, 0)
        
        # Calculate totals
        total_market_value = sum(p.market_value for p in positions.values())
        total_cost_basis = sum(p.cost_basis for p in positions.values())
        total_unrealized_pnl = total_market_value - total_cost_basis
        total_portfolio_value = total_market_value + cash
        
        return {
            'user_id': user_id,
            'cash': round(cash, 2),
            'total_market_value': round(total_market_value, 2),
            'total_cost_basis': round(total_cost_basis, 2),
            'total_unrealized_pnl': round(total_unrealized_pnl, 2),
            'total_unrealized_pnl_percent': round((total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0, 2),
            'total_portfolio_value': round(total_portfolio_value, 2),
            'positions_count': len(positions),
            'positions': [p.to_dict() for p in positions.values()],
        }
    
    def get_transactions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get transaction history"""
        if user_id not in self.transactions:
            return []
        
        return [t.to_dict() for t in self.transactions[user_id][-limit:]]


# Singleton instance
portfolio_manager = PortfolioManager()


def get_portfolio_manager() -> PortfolioManager:
    """Get portfolio manager instance"""
    return portfolio_manager
