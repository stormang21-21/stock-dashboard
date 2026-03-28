"""
Binance Provider

Cryptocurrency data from Binance API.
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


class BinanceProvider(BaseDataProvider):
    """
    Binance cryptocurrency data provider.
    
    Supports:
    - Spot market data
    - Multiple timeframes
    - Real-time prices
    """
    
    name = "binance"
    description = "Binance cryptocurrency exchange data"
    supported_markets = [MarketType.CRYPTO]
    supported_timeframes = [
        TimeFrame.DAILY,
        TimeFrame.WEEKLY,
        TimeFrame.MONTHLY,
        TimeFrame.MINUTE_1,
        TimeFrame.MINUTE_5,
        TimeFrame.MINUTE_15,
        "1h",
    ]
    rate_limit = 120  # 120 requests per minute
    base_url = "https://api.binance.com"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')  # Optional for public data
        self._client = None
    
    def _get_client(self):
        """Get HTTP client"""
        if self._client is None:
            try:
                import httpx
                headers = {}
                if self.api_key:
                    headers['X-MBX-APIKEY'] = self.api_key
                
                self._client = httpx.Client(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    headers=headers,
                )
            except Exception as e:
                raise DataFetchError(
                    message=f"Failed to create HTTP client: {e}",
                    source=self.name,
                )
        return self._client
    
    def _format_symbol(self, symbol: str) -> str:
        """
        Format crypto symbol for Binance.
        
        Args:
            symbol: Symbol like BTC, ETH, BTCUSDT
            
        Returns:
            Formatted symbol (e.g., BTCUSDT)
        """
        symbol = symbol.strip().upper().replace('-', '').replace('_', '')
        
        # Add USDT suffix if not present
        if not any(symbol.endswith(suffix) for suffix in ['USDT', 'BTC', 'ETH', 'BNB']):
            symbol = f"{symbol}USDT"
        
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
            symbol: Crypto symbol (e.g., BTC, ETH)
            date: Quote date
            
        Returns:
            QuoteData object
        """
        try:
            client = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Get kline data
            end_date = date or datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            response = client.get(
                '/api/v3/klines',
                params={
                    'symbol': formatted_symbol,
                    'interval': '1d',
                    'startTime': int(start_date.timestamp() * 1000),
                    'endTime': int(end_date.timestamp() * 1000),
                    'limit': 1,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise DataFetchError(
                    message=f"No data for {symbol}",
                    source=self.name,
                    symbol=symbol,
                )
            
            # Parse kline: [open_time, open, high, low, close, volume, ...]
            kline = data[0]
            
            return QuoteData(
                symbol=symbol,
                name=self._get_crypto_name(symbol),
                market=MarketType.CRYPTO,
                currency='USDT',
                timestamp=datetime.fromtimestamp(kline[0] / 1000),
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[5]),
                amount=float(kline[7]) if len(kline) > 7 else None,
            )
            
        except Exception as e:
            logger.error(f"Binance fetch failed for {symbol}: {e}")
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
            client = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Map timeframe to Binance interval
            interval_map = {
                TimeFrame.MINUTE_1: '1m',
                TimeFrame.MINUTE_5: '5m',
                TimeFrame.MINUTE_15: '15m',
                "1h": '1h',
                TimeFrame.DAILY: '1d',
                TimeFrame.WEEKLY: '1w',
                TimeFrame.MONTHLY: '1M',
            }
            
            interval = interval_map.get(timeframe, '1d')
            
            # Get klines
            response = client.get(
                '/api/v3/klines',
                params={
                    'symbol': formatted_symbol,
                    'interval': interval,
                    'startTime': int(start_date.timestamp() * 1000),
                    'endTime': int(end_date.timestamp() * 1000),
                    'limit': 1000,  # Max per request
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse klines
            quotes = []
            for kline in data:
                quote = QuoteData(
                    symbol=symbol,
                    name=self._get_crypto_name(symbol),
                    market=MarketType.CRYPTO,
                    currency='USDT',
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    amount=float(kline[7]) if len(kline) > 7 else None,
                )
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.error(f"Binance history fetch failed for {symbol}: {e}")
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
            client = self._get_client()
            formatted_symbol = self._format_symbol(symbol)
            
            # Get ticker
            response = client.get(
                '/api/v3/ticker/24hr',
                params={'symbol': formatted_symbol},
            )
            response.raise_for_status()
            
            data = response.json()
            
            return QuoteData(
                symbol=symbol,
                name=self._get_crypto_name(symbol),
                market=MarketType.CRYPTO,
                currency='USDT',
                timestamp=datetime.now(),
                open=float(data.get('openPrice', 0)),
                high=float(data.get('highPrice', 0)),
                low=float(data.get('lowPrice', 0)),
                close=float(data.get('lastPrice', 0)),
                volume=float(data.get('volume', 0)),
                amount=float(data.get('quoteVolume', 0)),
            )
            
        except Exception as e:
            logger.error(f"Binance realtime fetch failed for {symbol}: {e}")
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
        
        # Extract base symbol
        base = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '').replace('BNB', '')
        
        return names.get(base, f"{base} Token")
    
    @classmethod
    def register(cls):
        """Register provider"""
        DataProviderRegistry.register(cls)


# Add MINUTE_1H to TimeFrame

BinanceProvider.register()
