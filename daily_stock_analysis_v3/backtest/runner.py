"""
Strategy Runner

Execute trading strategies in backtest.
"""

from typing import List, Dict, Any, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

from data.providers.base import QuoteData
from portfolio.models import Portfolio


class StrategyRunner:
    """
    Run trading strategies.
    
    Wraps strategy logic for backtesting.
    """
    
    def __init__(self, strategy_class, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy runner.
        
        Args:
            strategy_class: Strategy class to instantiate
            config: Strategy configuration
        """
        self.strategy_class = strategy_class
        self.config = config or {}
        self.strategy = strategy_class(config)
        logger.info(f"StrategyRunner initialized: {strategy_class.name}")
    
    def generate_signals(
        self,
        quotes: List[QuoteData],
        portfolio: Optional[Portfolio] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals.
        
        Args:
            quotes: Current price quotes
            portfolio: Current portfolio state
            
        Returns:
            List of trading signals
        """
        try:
            signals = []
            
            for quote in quotes:
                # Get strategy signal for this stock
                signal = self.strategy.analyze_quote(quote, portfolio)
                
                if signal:
                    signals.append({
                        'stock_code': quote.symbol,
                        'stock_name': quote.name,
                        'action': signal.get('action'),
                        'quantity': signal.get('quantity'),
                        'confidence': signal.get('confidence', 0.5),
                        'reason': signal.get('reason', ''),
                    })
            
            return signals
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return []
