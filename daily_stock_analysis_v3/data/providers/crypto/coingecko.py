"""
CoinGecko Provider

Cryptocurrency data from CoinGecko API (free, no API key required).
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


class CoinGeckoProvider(BaseDataProvider):
    """
    CoinGecko cryptocurrency data provider.
    
    Free API, no key required for basic usage.
    """
    
    name = "coingecko"
    description = "CoinGecko cryptocurrency data (free API)"
    supported_markets = [MarketType.CRYPTO]
    supported_timeframes = [TimeFrame.DAILY]
    rate_limit = 30  # 30 requests per minute (free tier)
    base_url = "https://api.coingecko.com/api/v3"
    
    # CoinGecko IDs for major cryptos
    COIN_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'SOL': 'solana',
        'DOGE': 'dogecoin',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'LTC': 'litecoin',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'AVAX': 'avalanche-2',
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')  # Optional for Pro
        self._client = None
    
    def _get_client(self):
        """Get HTTP client"""
        if self._client is None:
            try:
                import httpx
                headers = {}
                if self.api_key:
                    headers['x-cg-pro-api-key'] = self.api_key
                
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
    
    def _symbol_to_id(self, symbol: str) -> str:
        """
        Convert symbol to CoinGecko ID.
        
        Args:
            symbol: Crypto symbol (e.g., BTC)
            
        Returns:
            CoinGecko ID
        """
        symbol = symbol.strip().upper()
        return self.COIN_IDS.get(symbol, symbol.lower())
    
    def get_quote(
        self,
        symbol: str,
        date: Optional[date] = None,
        **kwargs,
    ) -> QuoteData:
        """
        Get quote for cryptocurrency.
        
        Args:
            symbol: Crypto symbol
            date: Quote date
            
        Returns:
            QuoteData object
        """
        try:
            client = self._get_client()
            coin_id = self._symbol_to_id(symbol)
            
            # Get market data
            response = client.get(
                f'/coins/{coin_id}',
                params={
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false',
                },
            )
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get('market_data', {})
            
            # Get current price
            current_price = market_data.get('current_price', {}).get('usd', 0)
            
            return QuoteData(
                symbol=symbol,
                name=data.get('name', symbol),
                market=MarketType.CRYPTO,
                currency='USD',
                timestamp=datetime.now(),
                open=current_price,  # CoinGecko doesn't provide OHLC for current
                high=market_data.get('high_24h', {}).get('usd', current_price),
                low=market_data.get('low_24h', {}).get('usd', current_price),
                close=current_price,
                volume=market_data.get('total_volume', {}).get('usd', 0),
                amount=None,
            )
            
        except Exception as e:
            logger.error(f"CoinGecko fetch failed for {symbol}: {e}")
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
            coin_id = self._symbol_to_id(symbol)
            
            # Calculate days
            days = (end_date - start_date).days + 1
            
            # Get historical market data
            response = client.get(
                f'/coins/{coin_id}/market_chart',
                params={
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily',
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse prices
            quotes = []
            for price_data in data.get('prices', []):
                timestamp_ms, price = price_data
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                quote = QuoteData(
                    symbol=symbol,
                    name=self._symbol_to_id(symbol),
                    market=MarketType.CRYPTO,
                    currency='USD',
                    timestamp=timestamp,
                    open=price,  # CoinGecko provides close price only
                    high=price,
                    low=price,
                    close=price,
                    volume=0,
                    amount=None,
                )
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.error(f"CoinGecko history fetch failed for {symbol}: {e}")
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
        # Use get_quote for CoinGecko (no separate realtime endpoint)
        return self.get_quote(symbol)
    
    @classmethod
    def register(cls):
        """Register provider"""
        DataProviderRegistry.register(cls)


CoinGeckoProvider.register()
