"""
Base Strategy - Abstract base class for trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type
from datetime import date
import logging

logger = logging.getLogger(__name__)


class StrategySignal:
    """Trading signal from strategy"""
    
    def __init__(
        self,
        strategy_name: str,
        signal_type: str,  # buy/sell/hold
        confidence: float,  # 0-1
        price_target: Optional[float] = None,
        stop_loss: Optional[float] = None,
        reasoning: str = "",
    ):
        self.strategy_name = strategy_name
        self.signal_type = signal_type
        self.confidence = confidence
        self.price_target = price_target
        self.stop_loss = stop_loss
        self.reasoning = reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.strategy_name,
            'signal': self.signal_type,
            'confidence': self.confidence,
            'price_target': self.price_target,
            'stop_loss': self.stop_loss,
            'reasoning': self.reasoning,
        }


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    name = "base"
    description = "Base strategy"
    category = "general"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def analyze(
        self,
        stock_code: str,
        quotes: List[Dict[str, Any]],
        technical_indicators: Dict[str, Any],
        analysis_date: date,
    ) -> StrategySignal:
        """
        Analyze stock and generate signal.
        
        Args:
            stock_code: Stock symbol
            quotes: Historical price data
            technical_indicators: Technical indicators
            analysis_date: Analysis date
            
        Returns:
            StrategySignal
        """
        pass
    
    def supports_market(self, market: str) -> bool:
        """Check if strategy supports market"""
        return True  # Default: all markets
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return {}


class StrategyRegistry:
    """Registry for trading strategies"""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]) -> Type[BaseStrategy]:
        """Register a strategy class"""
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError("Must inherit from BaseStrategy")
        
        cls._strategies[strategy_class.name] = strategy_class
        logger.debug(f"Registered strategy: {strategy_class.name}")
        
        return strategy_class
    
    @classmethod
    def get_strategy(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseStrategy:
        """Get strategy instance"""
        if name not in cls._strategies:
            available = list(cls._strategies.keys())
            raise Exception(f"Strategy '{name}' not found. Available: {available}")
        
        strategy_class = cls._strategies[name]
        return strategy_class(config=config)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all registered strategies"""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_strategies_by_category(cls, category: str) -> List[str]:
        """Get strategies by category"""
        return [
            name for name, strategy in cls._strategies.items()
            if strategy.category == category
        ]
