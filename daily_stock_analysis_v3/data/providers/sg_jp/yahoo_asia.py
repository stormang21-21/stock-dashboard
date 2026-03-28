"""
Yahoo Asia Provider

Singapore and Japan stock data from Yahoo Finance.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.providers.base import BaseDataProvider, QuoteData, MarketType, TimeFrame, DataProviderRegistry
from exceptions import DataFetchError


class MarketSuffix:
    """Market suffixes for Yahoo Finance"""
    SG = ".SI"  # Singapore
    JP = ".T"   # Japan (Tokyo)


class YahooAsiaProvider(BaseDataProvider):
    """
    Yahoo Finance provider for Singapore and Japan stocks.
    
    Supports:
    - Singapore Exchange (SGX)
    - Tokyo Stock Exchange (TSE)
    """
    
    name = "yahoo_asia"
    description = "Singapore & Japan stock data from Yahoo Finance"
    supported_markets = [MarketType.SG, MarketType.JP]
    supported_timeframes = [TimeFrame.DAILY, TimeFrame.WEEKLY, TimeFrame.MONTHLY]
    rate_limit = 60  # 60 requests per minute
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        """Lazy import yfinance client"""
        if self._client is None:
            try:
                import yfinance as yf
                self._client = yf
            except ImportError:
                raise DataFetchError(
                    message="Yfinance not installed. Run: pip install yfinance",
                    source=self.name,
                )
        return self._client
    
    def _format_symbol(self, symbol: str, market: MarketType) -> str:
        """
        Format symbol with market suffix.
        
        Args:
            symbol: Stock symbol
            market: Market type
            
        Returns:
            Formatted symbol with suffix
        """
        symbol = symbol.strip().upper()
        
        if market == MarketType.SG:
            # Singapore stocks need .SI suffix
            if not symbol.endswith('.SI'):
                return f"{symbol}.SI"
        elif market == MarketType.JP:
            # Japan stocks need .T suffix
            if not symbol.endswith('.T'):
                return f"{symbol}.T"
        
        return symbol
    
    def _detect_market(self, symbol: str) -> MarketType:
        """
        Detect market from symbol format.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            MarketType
        """
        symbol = symbol.strip().upper()
        
        # Check suffix first
        if symbol.endswith('.SI'):
            return MarketType.SG
        elif symbol.endswith('.T'):
            return MarketType.JP
        
        # Singapore stocks often end with numbers or common suffixes
        if symbol.endswith(('S', 'SI')):
            return MarketType.SG
        
        # Default to Japan for numeric codes
        return MarketType.JP
    
    def get_quote(
        self,
        symbol: str,
        date: Optional[date] = None,
        market: Optional[MarketType] = None,
    ) -> QuoteData:
        """
        Get daily quote.
        
        Args:
            symbol: Stock symbol
            date: Quote date
            market: Market type
            
        Returns:
            QuoteData object
        """
        try:
            yf = self._get_client()
            
            # Auto-detect market if not provided
            if market is None:
                market = self._detect_market(symbol)
            
            formatted_symbol = self._format_symbol(symbol, market)
            
            # Download data
            ticker = yf.Ticker(formatted_symbol)
            
            # Get history
            end_date = date or datetime.now().date()
            
            df = ticker.history(
                start=end_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            
            if df.empty:
                raise DataFetchError(
                    message=f"No data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=market.value,
                )
            
            # Get latest row
            row = df.iloc[-1]
            
            # Get stock info
            info = ticker.info
            name = info.get('shortName', info.get('longName', symbol))
            
            # Determine currency based on market
            currency = info.get('currency', 'SGD' if market == MarketType.SG else 'JPY')
            
            return QuoteData(
                symbol=symbol,
                name=name,
                market=market,
                currency=currency,
                timestamp=row.name.to_pydatetime() if hasattr(row.name, 'to_pydatetime') else datetime.now(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                amount=None,
            )
            
        except Exception as e:
            logger.error(f"YahooAsia fetch failed for {symbol}: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                symbol=symbol,
            )
    
    def get_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: TimeFrame = TimeFrame.DAILY,
        market: Optional[MarketType] = None,
    ) -> List[QuoteData]:
        """
        Get historical data.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            market: Market type
            
        Returns:
            List of QuoteData objects
        """
        try:
            yf = self._get_client()
            
            # Auto-detect market if not provided
            if market is None:
                market = self._detect_market(symbol)
            
            formatted_symbol = self._format_symbol(symbol, market)
            
            # Download data
            ticker = yf.Ticker(formatted_symbol)
            
            # Map timeframe to yfinance interval
            interval_map = {
                TimeFrame.DAILY: "1d",
                TimeFrame.WEEKLY: "1wk",
                TimeFrame.MONTHLY: "1mo",
            }
            
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                interval=interval_map.get(timeframe, "1d"),
            )
            
            if df.empty:
                return []
            
            # Get stock info
            info = ticker.info
            name = info.get('shortName', info.get('longName', symbol))
            currency = info.get('currency', 'SGD' if market == MarketType.SG else 'JPY')
            
            # Convert to QuoteData list
            quotes = []
            for idx, row in df.iterrows():
                quote = QuoteData(
                    symbol=symbol,
                    name=name,
                    market=market,
                    currency=currency,
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.now(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    amount=None,
                )
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.error(f"YahooAsia history fetch failed for {symbol}: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                symbol=symbol,
            )
    
    def get_realtime_quote(
        self,
        symbol: str,
        market: Optional[MarketType] = None,
    ) -> QuoteData:
        """
        Get real-time quote.
        
        Args:
            symbol: Stock symbol
            market: Market type
            
        Returns:
            QuoteData with latest price
        """
        try:
            yf = self._get_client()
            
            # Auto-detect market if not provided
            if market is None:
                market = self._detect_market(symbol)
            
            formatted_symbol = self._format_symbol(symbol, market)
            
            # Get ticker
            ticker = yf.Ticker(formatted_symbol)
            
            # Get fast info
            info = ticker.fast_info or ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                raise DataFetchError(
                    message=f"Realtime price not available for {symbol}",
                    source=self.name,
                    symbol=symbol,
                )
            
            name = info.get('shortName', info.get('longName', symbol))
            currency = info.get('currency', 'SGD' if market == MarketType.SG else 'JPY')
            
            return QuoteData(
                symbol=symbol,
                name=name,
                market=market,
                currency=currency,
                timestamp=datetime.now(),
                open=float(info.get('open', current_price)),
                high=float(info.get('dayHigh', current_price)),
                low=float(info.get('dayLow', current_price)),
                close=float(current_price),
                volume=int(info.get('volume', 0)),
                amount=None,
            )
            
        except Exception as e:
            logger.error(f"YahooAsia realtime fetch failed for {symbol}: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                symbol=symbol,
            )
    
    @classmethod
    def register(cls):
        """Register provider"""
        DataProviderRegistry.register(cls)


# Auto-register on import
YahooAsiaProvider.register()
