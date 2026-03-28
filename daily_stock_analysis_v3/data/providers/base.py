"""
Base Data Provider - Abstract base class for all data providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, date
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class MarketType(str):
    """Market types"""
    CN = "cn"           # China A-shares
    HK = "hk"           # Hong Kong
    US = "us"           # United States
    SG = "sg"           # Singapore
    JP = "jp"           # Japan
    CRYPTO = "crypto"   # Cryptocurrency


class TimeFrame(str):
    """K-line timeframes"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    MINUTE_60 = "60m"


class QuoteData:
    """Standardized quote data structure"""
    
    def __init__(self, symbol, name, market, currency, timestamp, open, high, low, close, volume, amount=None, **kwargs):
        self.symbol = symbol
        self.name = name
        self.market = market
        self.currency = currency
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.amount = amount
        self.extra = kwargs
    
    def to_dict(self):
        return {
            "symbol": self.symbol, "name": self.name, "market": self.market.value if isinstance(self.market, MarketType) else self.market,
            "currency": self.currency, "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            "open": self.open, "high": self.high, "low": self.low, "close": self.close, "volume": self.volume, "amount": self.amount, **self.extra
        }
    
    def __repr__(self):
        return f"QuoteData(symbol={self.symbol}, close={self.close})"


class BaseDataProvider(ABC):
    """Abstract base class for data providers"""
    
    name = "base"
    description = "Base provider"
    supported_markets = []
    supported_timeframes = [TimeFrame.DAILY]
    rate_limit = None
    
    def __init__(self, config=None):
        self.config = config or {}
    
    @abstractmethod
    def get_quote(self, symbol, date=None):
        pass
    
    @abstractmethod
    def get_history(self, symbol, start_date, end_date, timeframe=TimeFrame.DAILY):
        pass
    
    @abstractmethod
    def get_realtime_quote(self, symbol):
        pass
    
    def supports_market(self, market):
        return market in self.supported_markets
    
    def supports_timeframe(self, timeframe):
        return timeframe in self.supported_timeframes


class DataProviderRegistry:
    """Registry for data providers"""
    
    _providers = {}
    
    @classmethod
    def register(cls, provider_class):
        if not issubclass(provider_class, BaseDataProvider):
            raise TypeError("Must inherit from BaseDataProvider")
        cls._providers[provider_class.name] = provider_class
        return provider_class
    
    @classmethod
    def get_provider(cls, name, config=None):
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise Exception(f"Provider '{name}' not found. Available: {available}")
        return cls._providers[name](config=config)
    
    @classmethod
    def list_providers(cls):
        return list(cls._providers.keys())
    
    @classmethod
    def get_providers_for_market(cls, market):
        return [name for name, p in cls._providers.items() if market in p.supported_markets]
