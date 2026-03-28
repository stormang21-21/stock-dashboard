"""
Yahoo Crypto Provider

Cryptocurrency data from Yahoo Finance.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.providers.base import BaseDataProvider, QuoteData, MarketType, TimeFrame, DataProviderRegistry
from exceptions import DataFetchError


class YahooCryptoProvider(BaseDataProvider):
    """
    Yahoo Finance cryptocurrency data provider.
    
    Uses yfinance library for crypto data.
    """
    
    name = "yahoo_crypto"
    description = "Yahoo Finance cryptocurrency data"
    supported_markets = [MarketType.CRYPTO]
    supported_timeframes = [
        TimeFrame.DAILY,
        TimeFrame.WEEKLY,
        TimeFrame.MONTHLY,
        "1h",
    ]
    rate_limit = 60  # 60 requests per minute
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        """Get yfinance client"""
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
    
    def _format_symbol(self, symbol: str) -> str:
        """
        Format crypto symbol for Yahoo Finance.
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            
        Returns:
            Formatted symbol (e.g., BTC-USD)
        """
        symbol = symbol.strip().upper()
        
        # Add -USD suffix if not present
        if not any('-' in symbol for suffix in ['USD', 'BTC', 'ETH', 'EUR']):
            symbol = f"{symbol}-USD"
        
        return symbol
    
    def get_quote(
        self,
        symbol: str,
        date: Optional[date] = None,
        **kwargs,
    ) -> QuoteData:
        """
        Get daily quote for cryptocurrency.
        
        Args:
            symbol: Crypto symbol
            date: Quote date
            
        Returns:
            QuoteData object
        """
        try:
            yf = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Get ticker
            ticker = yf.Ticker(formatted_symbol)
            
            # Get history
            end_date = date or datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            
            if df.empty:
                raise DataFetchError(
                    message=f"No data for {symbol}",
                    source=self.name,
                    symbol=symbol,
                )
            
            # Get latest row
            row = df.iloc[-1]
            
            return QuoteData(
                symbol=symbol,
                name=self._get_crypto_name(symbol),
                market=MarketType.CRYPTO,
                currency='USD',
                timestamp=row.name.to_pydatetime() if hasattr(row.name, 'to_pydatetime') else datetime.now(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                amount=None,
            )
            
        except Exception as e:
            logger.error(f"Yahoo Crypto fetch failed for {symbol}: {e}")
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
        **kwargs,
    ) -> List[QuoteData]:
        """
        Get historical data.
        
        Args:
            symbol: Crypto symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            
        Returns:
            List of QuoteData objects
        """
        try:
            yf = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Get ticker
            ticker = yf.Ticker(formatted_symbol)
            
            # Map timeframe
            interval_map = {
                TimeFrame.DAILY: "1d",
                TimeFrame.WEEKLY: "1wk",
                TimeFrame.MONTHLY: "1mo",
                "1h": "1h",
            }
            
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval=interval_map.get(timeframe, "1d"),
            )
            
            if df.empty:
                return []
            
            # Convert to QuoteData list
            quotes = []
            for idx, row in df.iterrows():
                quote = QuoteData(
                    symbol=symbol,
                    name=self._get_crypto_name(symbol),
                    market=MarketType.CRYPTO,
                    currency='USD',
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
            logger.error(f"Yahoo Crypto history fetch failed for {symbol}: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                symbol=symbol,
            )
    
    def get_realtime_quote(self, symbol: str, **kwargs) -> QuoteData:
        """
        Get real-time price.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            QuoteData with latest price
        """
        try:
            yf = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Get ticker
            ticker = yf.Ticker(formatted_symbol)
            
            # Get fast info
            info = ticker.fast_info or ticker.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                raise DataFetchError(
                    message=f"Realtime price not available for {symbol}",
                    source=self.name,
                    symbol=symbol,
                )
            
            return QuoteData(
                symbol=symbol,
                name=self._get_crypto_name(symbol),
                market=MarketType.CRYPTO,
                currency='USD',
                timestamp=datetime.now(),
                open=float(info.get('open', current_price)),
                high=float(info.get('dayHigh', current_price)),
                low=float(info.get('dayLow', current_price)),
                close=float(current_price),
                volume=int(info.get('volume', 0)),
                amount=None,
            )
            
        except Exception as e:
            logger.error(f"Yahoo Crypto realtime fetch failed for {symbol}: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                symbol=symbol,
            )
    
    def _get_crypto_name(self, symbol: str) -> str:
        """Get cryptocurrency name"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'Binance Coin',
            'XRP': 'Ripple',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'DOT': 'Polkadot',
            'MATIC': 'Polygon',
            'LTC': 'Litecoin',
        }
        
        base = symbol.replace('-USD', '').replace('-BTC', '').replace('-ETH', '')
        return names.get(base, f"{base} Cryptocurrency")
    
    @classmethod
    def register(cls):
        """Register provider"""
        DataProviderRegistry.register(cls)


YahooCryptoProvider.register()
