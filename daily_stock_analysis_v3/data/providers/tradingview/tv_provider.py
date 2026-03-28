"""
TradingView Provider

Technical analysis data from TradingView.
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


class TradingViewProvider(BaseDataProvider):
    """
    TradingView technical analysis provider.
    
    Provides:
    - Technical indicators
    - Oscillators
    - Moving averages
    - Pivot points
    - Market screener data
    """
    
    name = "tradingview"
    description = "TradingView technical analysis & indicators"
    supported_markets = [MarketType.CN, MarketType.HK, MarketType.US, MarketType.SG, MarketType.JP, MarketType.CRYPTO]
    supported_timeframes = [TimeFrame.DAILY, TimeFrame.WEEKLY, TimeFrame.MONTHLY]
    rate_limit = 60  # 60 requests per minute
    base_url = "https://scanner.tradingview.com"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        """Get HTTP client"""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0',
                        'Content-Type': 'application/json',
                    },
                )
            except Exception as e:
                raise DataFetchError(
                    message=f"Failed to create HTTP client: {e}",
                    source=self.name,
                )
        return self._client
    
    def get_technical_analysis(
        self,
        symbol: str,
        market: MarketType,
        timeframe: str = "1D",
    ) -> Dict[str, Any]:
        """
        Get TradingView technical analysis summary.
        
        Args:
            symbol: Stock/crypto symbol
            market: Market type
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1D, 1W, 1M)
            
        Returns:
            Technical analysis summary
        """
        try:
            client = self._get_client()
            
            # Map market to TradingView exchange
            exchange_map = {
                MarketType.US: "NASDAQ",
                MarketType.CN: "SSE",
                MarketType.HK: "HKEX",
                MarketType.SG: "SGX",
                MarketType.JP: "TSE",
                MarketType.CRYPTO: "BINANCE",
            }
            
            exchange = exchange_map.get(market, "NASDAQ")
            
            # Build screener request
            payload = {
                "symbols": {
                    "tickers": [f"{exchange}:{symbol}"],
                    "query": {"types": []},
                },
                "columns": [
                    "Recommend.Other",
                    "Recommend.All",
                    "Recommend.MA",
                    "RSI",
                    "RSI[1]",
                    "Stoch.K",
                    "Stoch.D",
                    "Stoch.K[1]",
                    "Stoch.D[1]",
                    "CCI20",
                    "CCI20[1]",
                    "ADX",
                    "ADX+DI",
                    "ADX-DI",
                    "ADX+DI[1]",
                    "ADX-DI[1]",
                    "AO",
                    "AO[1]",
                    "Mom",
                    "Mom[1]",
                    "MACD.macd",
                    "MACD.signal",
                    "Rec.Stoch.RSI",
                    "Rec.WR",
                    "Rec.BBPower",
                    "Rec.UO",
                    "EMA10",
                    "close",
                    "SMA10",
                    "EMA20",
                    "SMA20",
                    "EMA30",
                    "SMA30",
                    "EMA50",
                    "SMA50",
                    "EMA100",
                    "SMA100",
                    "EMA200",
                    "SMA200",
                    "Rec.Ichimoku",
                    "Rec.VWMA",
                    "Rec.HullMA9",
                    "Pivot.M.Classic.S3",
                    "Pivot.M.Classic.S2",
                    "Pivot.M.Classic.S1",
                    "Pivot.M.Classic.Middle",
                    "Pivot.M.Classic.R1",
                    "Pivot.M.Classic.R2",
                    "Pivot.M.Classic.R3",
                ],
                "filter": {"left": 0, "right": 0},
            }
            
            response = client.post(
                "/global/screener/screen/",
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('data'):
                return self._get_empty_analysis()
            
            result = data['data'][0]['d']
            
            return {
                'symbol': symbol,
                'market': market.value,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'recommendation': self._parse_recommendation(result[1]),
                    'oscillators': self._parse_oscillators(result),
                    'moving_averages': self._parse_moving_averages(result),
                },
                'indicators': {
                    'rsi': result[3] if result[3] else None,
                    'stochastic_k': result[5] if result[5] else None,
                    'stochastic_d': result[6] if result[6] else None,
                    'cci': result[9] if result[9] else None,
                    'adx': result[12] if result[12] else None,
                    'awesome_oscillator': result[17] if result[17] else None,
                    'momentum': result[19] if result[19] else None,
                    'macd': result[21] if result[21] else None,
                    'macd_signal': result[22] if result[22] else None,
                },
                'moving_averages': {
                    'ema10': result[26] if result[26] else None,
                    'sma10': result[28] if result[28] else None,
                    'ema20': result[29] if result[29] else None,
                    'sma20': result[31] if result[31] else None,
                    'ema50': result[35] if result[35] else None,
                    'sma50': result[37] if result[37] else None,
                    'ema200': result[41] if result[41] else None,
                    'sma200': result[43] if result[43] else None,
                },
                'pivot_points': {
                    'r3': result[50] if result[50] else None,
                    'r2': result[51] if result[51] else None,
                    'r1': result[52] if result[52] else None,
                    'middle': result[53] if result[53] else None,
                    's1': result[54] if result[54] else None,
                    's2': result[55] if result[55] else None,
                    's3': result[56] if result[56] else None,
                },
            }
            
        except Exception as e:
            logger.error(f"TradingView analysis failed for {symbol}: {e}")
            return self._get_empty_analysis()
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'symbol': '',
            'market': '',
            'timeframe': '',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'recommendation': 'NEUTRAL',
                'oscillators': {'buy': 0, 'sell': 0, 'neutral': 0},
                'moving_averages': {'buy': 0, 'sell': 0, 'neutral': 0},
            },
            'indicators': {},
            'moving_averages': {},
            'pivot_points': {},
        }
    
    def _parse_recommendation(self, value: Optional[float]) -> str:
        """Parse recommendation score"""
        if value is None:
            return 'NEUTRAL'
        elif value >= 0.5:
            return 'STRONG_BUY'
        elif value >= 0.2:
            return 'BUY'
        elif value <= -0.5:
            return 'STRONG_SELL'
        elif value <= -0.2:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    def _parse_oscillators(self, result: List) -> Dict[str, int]:
        """Parse oscillator signals"""
        return {
            'buy': 0,
            'sell': 0,
            'neutral': 0,
        }
    
    def _parse_moving_averages(self, result: List) -> Dict[str, int]:
        """Parse moving average signals"""
        return {
            'buy': 0,
            'sell': 0,
            'neutral': 0,
        }
    
    def get_quote(
        self,
        symbol: str,
        date: Optional[date] = None,
        **kwargs,
    ) -> QuoteData:
        """
        Get quote (not primary use case for TradingView).
        
        TradingView is primarily for technical analysis, not price data.
        Use other providers for OHLCV data.
        """
        raise NotImplementedError(
            "TradingView provider is for technical analysis only. "
            "Use Binance, YFinance, or other providers for price data."
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
        Get historical data (not supported).
        
        TradingView doesn't provide historical OHLCV via public API.
        """
        raise NotImplementedError(
            "TradingView doesn't provide historical OHLCV via public API. "
            "Use other providers for historical data."
        )
    
    def get_realtime_quote(self, symbol: str, **kwargs) -> QuoteData:
        """
        Get real-time quote (not supported).
        
        Use other providers for real-time prices.
        """
        raise NotImplementedError(
            "TradingView doesn't provide real-time quotes via public API. "
            "Use other providers for price data."
        )
    
    @classmethod
    def register(cls):
        """Register provider"""
        DataProviderRegistry.register(cls)


TradingViewProvider.register()
