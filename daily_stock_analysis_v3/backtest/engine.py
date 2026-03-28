"""
Backtest Engine

Core backtesting engine for strategy evaluation.
"""

from typing import List, Dict, Any, Optional, Type
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.models import Portfolio, Trade, TradeType, TradeStatus
from portfolio.tracker import PortfolioTracker
from data.providers.base import QuoteData


class BacktestConfig:
    """Backtest configuration"""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,  # 0.1%
        slippage: float = 0.001,  # 0.1%
        position_size_pct: float = 0.1,  # 10% per position
        max_positions: int = 10,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'initial_capital': self.initial_capital,
            'commission_rate': self.commission_rate,
            'slippage': self.slippage,
            'position_size_pct': self.position_size_pct,
            'max_positions': self.max_positions,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
        }


class BacktestEngine:
    """
    Core backtesting engine.
    
    Simulates trading strategy on historical data.
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine.
        
        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()
        self.portfolio: Optional[Portfolio] = None
        self.tracker: Optional[PortfolioTracker] = None
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.current_date: Optional[date] = None
        logger.info("BacktestEngine initialized")
    
    def initialize(self, start_date: date, initial_capital: Optional[float] = None) -> None:
        """
        Initialize backtest.
        
        Args:
            start_date: Backtest start date
            initial_capital: Starting capital
        """
        capital = initial_capital or self.config.initial_capital
        
        self.portfolio = Portfolio(
            id=f"backtest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name="Backtest Portfolio",
        )
        self.portfolio.cash_balance = capital
        
        self.tracker = PortfolioTracker(self.portfolio)
        self.trades = []
        self.equity_curve = []
        self.current_date = start_date
        
        # Record initial snapshot
        self._record_snapshot()
        
        logger.info(f"Backtest initialized with ${capital:,.2f}")
    
    def process_signal(
        self,
        signal: Dict[str, Any],
        quote: QuoteData,
    ) -> Optional[Trade]:
        """
        Process trading signal.
        
        Args:
            signal: Trading signal with action, quantity, etc.
            quote: Current price quote
            
        Returns:
            Executed trade or None
        """
        action = signal.get('action', '').lower()
        stock_code = signal.get('stock_code')
        stock_name = signal.get('stock_name', stock_code)
        
        if not action or not stock_code:
            return None
        
        # Calculate position size
        position_value = self.portfolio.cash_balance * self.config.position_size_pct
        quantity = position_value / quote.close
        
        # Apply slippage
        if action == 'buy':
            exec_price = quote.close * (1 + self.config.slippage)
        else:  # sell
            exec_price = quote.close * (1 - self.config.slippage)
        
        # Calculate commission
        commission = quantity * exec_price * self.config.commission_rate
        
        try:
            if action == 'buy':
                # Check if we can open new position
                if self.portfolio.position_count >= self.config.max_positions:
                    logger.debug(f"Max positions reached, skipping buy")
                    return None
                
                # Check sufficient cash
                total_cost = (quantity * exec_price) + commission
                if total_cost > self.portfolio.cash_balance:
                    logger.debug(f"Insufficient cash for buy")
                    return None
                
                trade = self.tracker.buy(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    quantity=quantity,
                    price=exec_price,
                    commission=commission,
                    trade_date=self.current_date,
                )
                
            elif action == 'sell':
                # Check if we have position
                if stock_code not in self.portfolio.positions:
                    logger.debug(f"No position to sell: {stock_code}")
                    return None
                
                position = self.portfolio.positions[stock_code]
                if position.quantity <= 0:
                    logger.debug(f"Zero position to sell: {stock_code}")
                    return None
                
                # Sell all or specified quantity
                sell_quantity = signal.get('quantity', position.quantity)
                sell_quantity = min(sell_quantity, position.quantity)
                
                trade = self.tracker.sell(
                    stock_code=stock_code,
                    quantity=sell_quantity,
                    price=exec_price,
                    commission=commission,
                    trade_date=self.current_date,
                )
            
            else:
                logger.debug(f"Unknown action: {action}")
                return None
            
            # Record trade
            self.trades.append({
                'date': self.current_date.isoformat(),
                'action': action,
                'stock_code': stock_code,
                'quantity': trade.quantity,
                'price': trade.price,
                'commission': trade.commission,
                'total_value': trade.total_value,
                'signal': signal,
            })
            
            logger.info(f"Backtest {action}: {trade.quantity:.2f} {stock_code} @ ${trade.price:.2f}")
            return trade
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return None
    
    def process_day(
        self,
        date: date,
        quotes: List[QuoteData],
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Process single day of backtest.
        
        Args:
            date: Current date
            quotes: Price quotes for all stocks
            signals: Optional trading signals
            
        Returns:
            Day summary
        """
        self.current_date = date
        
        # Update prices
        prices = {q.symbol: q.close for q in quotes}
        self.tracker.update_prices(prices)
        
        # Process signals
        if signals:
            for signal in signals:
                # Find matching quote
                stock_code = signal.get('stock_code')
                quote = next((q for q in quotes if q.symbol == stock_code), None)
                
                if quote:
                    self.process_signal(signal, quote)
        
        # Record snapshot
        snapshot = self._record_snapshot()
        
        return {
            'date': date.isoformat(),
            'equity': snapshot['total_equity'],
            'cash': snapshot['cash_balance'],
            'market_value': snapshot['market_value'],
            'positions': snapshot['position_count'],
            'trades_today': len([t for t in self.trades if t['date'] == date.isoformat()]),
        }
    
    def run(
        self,
        quotes_history: Dict[str, List[QuoteData]],
        strategy,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Run complete backtest.
        
        Args:
            quotes_history: Historical quotes by stock code
            strategy: Strategy object with generate_signals() method
            start_date: Backtest start
            end_date: Backtest end
            
        Returns:
            Backtest results
        """
        logger.info(f"Starting backtest: {start_date} to {end_date}")
        
        # Initialize
        self.initialize(start_date)
        
        # Get all dates
        all_dates = set()
        for quotes in quotes_history.values():
            for q in quotes:
                all_dates.add(q.timestamp.date())
        
        all_dates = sorted([d for d in all_dates if start_date <= d <= end_date])
        
        if not all_dates:
            logger.warning("No trading days in range")
            return {'error': 'No trading days'}
        
        # Process each day
        for current_date in all_dates:
            # Get quotes for this date
            day_quotes = []
            for stock_code, quotes in quotes_history.items():
                day_quote = next((q for q in quotes if q.timestamp.date() == current_date), None)
                if day_quote:
                    day_quotes.append(day_quote)
            
            if not day_quotes:
                continue
            
            # Generate signals
            signals = strategy.generate_signals(day_quotes, self.portfolio)
            
            # Process day
            self.process_day(current_date, day_quotes, signals)
        
        logger.info(f"Backtest complete: {len(self.trades)} trades")
        
        return self.get_results()
    
    def _record_snapshot(self) -> Dict[str, Any]:
        """Record equity snapshot"""
        snapshot = self.tracker.take_snapshot()
        self.equity_curve.append(snapshot)
        return snapshot
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get backtest results.
        
        Returns:
            Results dictionary
        """
        if not self.equity_curve:
            return {'error': 'No data'}
        
        final_snapshot = self.equity_curve[-1]
        initial_snapshot = self.equity_curve[0]
        
        return {
            'config': self.config.to_dict(),
            'start_date': initial_snapshot['date'],
            'end_date': final_snapshot['date'],
            'trading_days': len(self.equity_curve),
            'initial_capital': initial_snapshot['total_equity'],
            'final_equity': final_snapshot['total_equity'],
            'total_return': ((final_snapshot['total_equity'] - initial_snapshot['total_equity']) / initial_snapshot['total_equity']) * 100,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in self.trades if t.get('pnl', 0) < 0]),
            'equity_curve': self.equity_curve,
            'trades': self.trades,
        }
