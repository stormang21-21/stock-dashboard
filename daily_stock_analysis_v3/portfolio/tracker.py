"""
Portfolio Tracker

Track portfolio performance over time.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

from portfolio.models import Portfolio, Position, Trade, CashFlow, TradeType, TradeStatus


class PortfolioTracker:
    """
    Track portfolio performance and holdings.
    
    Features:
    - Real-time position tracking
    - Trade management
    - Cash flow tracking
    - Performance snapshots
    """
    
    def __init__(self, portfolio: Portfolio):
        """
        Initialize tracker.
        
        Args:
            portfolio: Portfolio to track
        """
        self.portfolio = portfolio
        self.snapshots: List[Dict[str, Any]] = []
        logger.info(f"PortfolioTracker initialized for {portfolio.name}")
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update prices for all positions.
        
        Args:
            prices: Dictionary of stock_code -> price
        """
        updated = 0
        for stock_code, price in prices.items():
            if stock_code in self.portfolio.positions:
                position = self.portfolio.positions[stock_code]
                position.update_price(price)
                updated += 1
        
        logger.info(f"Updated prices for {updated} positions")
    
    def buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        currency: Optional[str] = None,
        trade_date: Optional[date] = None,
    ) -> Trade:
        """
        Execute buy trade.
        
        Args:
            stock_code: Stock symbol
            stock_name: Stock name
            quantity: Number of shares
            price: Price per share
            commission: Trade commission
            currency: Currency
            trade_date: Trade date
            
        Returns:
            Executed trade
        """
        trade = Trade(
            id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            portfolio_id=self.portfolio.id,
            stock_code=stock_code,
            stock_name=stock_name,
            trade_type=TradeType.BUY,
            quantity=quantity,
            price=price,
            commission=commission,
            currency=currency or self.portfolio.base_currency,
            trade_date=trade_date or date.today(),
        )
        
        # Check sufficient cash
        if trade.total_value > self.portfolio.cash_balance:
            raise ValueError(f"Insufficient cash: need {trade.total_value}, have {self.portfolio.cash_balance}")
        
        trade.execute()
        self.portfolio.add_trade(trade)
        
        logger.info(f"Buy executed: {quantity} {stock_code} @ {price}")
        return trade
    
    def sell(
        self,
        stock_code: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        trade_date: Optional[date] = None,
    ) -> Trade:
        """
        Execute sell trade.
        
        Args:
            stock_code: Stock symbol
            quantity: Number of shares
            price: Price per share
            commission: Trade commission
            trade_date: Trade date
            
        Returns:
            Executed trade
        """
        # Check sufficient position
        if stock_code not in self.portfolio.positions:
            raise ValueError(f"No position in {stock_code}")
        
        position = self.portfolio.positions[stock_code]
        if position.quantity < quantity:
            raise ValueError(f"Insufficient position: have {position.quantity}, selling {quantity}")
        
        trade = Trade(
            id=f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            portfolio_id=self.portfolio.id,
            stock_code=stock_code,
            stock_name=position.stock_name,
            trade_type=TradeType.SELL,
            quantity=quantity,
            price=price,
            commission=commission,
            currency=position.currency,
            trade_date=trade_date or date.today(),
        )
        
        trade.execute()
        self.portfolio.add_trade(trade)
        
        logger.info(f"Sell executed: {quantity} {stock_code} @ {price}")
        return trade
    
    def deposit(self, amount: float, currency: Optional[str] = None, description: str = "") -> CashFlow:
        """
        Record cash deposit.
        
        Args:
            amount: Deposit amount
            currency: Currency
            description: Description
            
        Returns:
            Cash flow record
        """
        cash_flow = CashFlow(
            id=f"flow_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            portfolio_id=self.portfolio.id,
            flow_type="deposit",
            amount=amount,
            currency=currency or self.portfolio.base_currency,
            description=description,
        )
        
        self.portfolio.add_cash_flow(cash_flow)
        logger.info(f"Deposit recorded: {amount} {cash_flow.currency}")
        return cash_flow
    
    def withdraw(self, amount: float, currency: Optional[str] = None, description: str = "") -> CashFlow:
        """
        Record cash withdrawal.
        
        Args:
            amount: Withdrawal amount
            currency: Currency
            description: Description
            
        Returns:
            Cash flow record
        """
        if amount > self.portfolio.cash_balance:
            raise ValueError(f"Insufficient cash: need {amount}, have {self.portfolio.cash_balance}")
        
        cash_flow = CashFlow(
            id=f"flow_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            portfolio_id=self.portfolio.id,
            flow_type="withdrawal",
            amount=amount,
            currency=currency or self.portfolio.base_currency,
            description=description,
        )
        
        self.portfolio.add_cash_flow(cash_flow)
        logger.info(f"Withdrawal recorded: {amount} {cash_flow.currency}")
        return cash_flow
    
    def record_dividend(
        self,
        stock_code: str,
        amount: float,
        currency: Optional[str] = None,
        description: str = "",
    ) -> CashFlow:
        """
        Record dividend payment.
        
        Args:
            stock_code: Stock symbol
            amount: Dividend amount
            currency: Currency
            description: Description
            
        Returns:
            Cash flow record
        """
        cash_flow = CashFlow(
            id=f"div_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            portfolio_id=self.portfolio.id,
            flow_type="dividend",
            amount=amount,
            currency=currency or self.portfolio.base_currency,
            description=description or f"Dividend from {stock_code}",
            reference=stock_code,
        )
        
        self.portfolio.add_cash_flow(cash_flow)
        logger.info(f"Dividend recorded: {amount} {cash_flow.currency} from {stock_code}")
        return cash_flow
    
    def take_snapshot(self) -> Dict[str, Any]:
        """
        Take portfolio snapshot.
        
        Returns:
            Snapshot dictionary
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'date': date.today().isoformat(),
            'total_equity': self.portfolio.total_equity,
            'cash_balance': self.portfolio.cash_balance,
            'market_value': self.portfolio.total_market_value,
            'cost_basis': self.portfolio.total_cost_basis,
            'unrealized_pnl': self.portfolio.total_unrealized_pnl,
            'return_percent': self.portfolio.total_return_percent,
            'position_count': self.portfolio.position_count,
            'positions': {
                code: {
                    'quantity': pos.quantity,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'return_percent': pos.unrealized_pnl_percent,
                }
                for code, pos in self.portfolio.positions.items()
                if pos.quantity != 0
            },
        }
        
        self.snapshots.append(snapshot)
        logger.info(f"Snapshot taken: equity={snapshot['total_equity']:.2f}")
        return snapshot
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary.
        
        Returns:
            Summary dictionary
        """
        return {
            'name': self.portfolio.name,
            'base_currency': self.portfolio.base_currency,
            'total_equity': self.portfolio.total_equity,
            'cash_balance': self.portfolio.cash_balance,
            'market_value': self.portfolio.total_market_value,
            'cost_basis': self.portfolio.total_cost_basis,
            'unrealized_pnl': self.portfolio.total_unrealized_pnl,
            'return_percent': self.portfolio.total_return_percent,
            'position_count': self.portfolio.position_count,
            'trade_count': len(self.portfolio.trades),
            'snapshots': len(self.snapshots),
        }
