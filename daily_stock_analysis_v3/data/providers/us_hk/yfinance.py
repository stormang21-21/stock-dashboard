"""YFinance Provider - US/HK stock data"""

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


class YFinanceProvider(BaseDataProvider):
    """YFinance provider for US/HK stocks"""
    
    name = "yfinance"
    description = "US/HK stock data from Yahoo Finance"
    supported_markets = [MarketType.US, MarketType.HK]
    supported_timeframes = [TimeFrame.DAILY, TimeFrame.WEEKLY, TimeFrame.MONTHLY]
    rate_limit = 60
    
    def __init__(self, config=None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import yfinance as yf
                self._client = yf
            except ImportError:
                raise DataFetchError("Yfinance not installed. Run: pip install yfinance", source=self.name)
        return self._client
    
    def _format_symbol(self, symbol, market):
        symbol = symbol.strip().upper()
        if market == MarketType.HK and not symbol.endswith('.HK'):
            return f"{symbol}.HK"
        elif market == MarketType.US:
            symbol = symbol.replace('.HK', '').replace('.SS', '').replace('.SZ', '')
        return symbol
    
    def get_quote(self, symbol, date=None, market=None):
        try:
            yf = self._get_client()
            
            if market is None:
                market = MarketType.HK if symbol.startswith('0') else MarketType.US
            
            formatted = self._format_symbol(symbol, market)
            ticker = yf.Ticker(formatted)
            
            end_date = date or datetime.now().date()
            df = ticker.history(
                start=end_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            
            if df.empty:
                raise DataFetchError(f"No data for {symbol}", source=self.name, symbol=symbol)
            
            row = df.iloc[-1]
            info = ticker.info
            name = info.get('shortName', info.get('longName', symbol))
            currency = info.get('currency', 'USD' if market == MarketType.US else 'HKD')
            
            return QuoteData(
                symbol=symbol, name=name, market=market, currency=currency,
                timestamp=row.name.to_pydatetime() if hasattr(row.name, 'to_pydatetime') else datetime.now(),
                open=float(row['Open']), high=float(row['High']), low=float(row['Low']),
                close=float(row['Close']), volume=int(row['Volume']), amount=None,
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_history(self, symbol, start_date, end_date, timeframe=TimeFrame.DAILY, market=None):
        try:
            yf = self._get_client()
            
            if market is None:
                market = MarketType.HK if symbol.startswith('0') else MarketType.US
            
            formatted = self._format_symbol(symbol, market)
            ticker = yf.Ticker(formatted)
            
            interval_map = {TimeFrame.DAILY: "1d", TimeFrame.WEEKLY: "1wk", TimeFrame.MONTHLY: "1mo"}
            
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                interval=interval_map.get(timeframe, "1d"),
            )
            
            if df.empty:
                return []
            
            info = ticker.info
            name = info.get('shortName', info.get('longName', symbol))
            currency = info.get('currency', 'USD' if market == MarketType.US else 'HKD')
            
            quotes = []
            for idx, row in df.iterrows():
                quotes.append(QuoteData(
                    symbol=symbol, name=name, market=market, currency=currency,
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.now(),
                    open=float(row['Open']), high=float(row['High']), low=float(row['Low']),
                    close=float(row['Close']), volume=int(row['Volume']), amount=None,
                ))
            
            return quotes
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_realtime_quote(self, symbol, market=None):
        try:
            yf = self._get_client()
            
            if market is None:
                market = MarketType.HK if symbol.startswith('0') else MarketType.US
            
            formatted = self._format_symbol(symbol, market)
            ticker = yf.Ticker(formatted)
            info = ticker.fast_info or ticker.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                raise DataFetchError(f"Realtime price not available for {symbol}", source=self.name, symbol=symbol)
            
            name = info.get('shortName', info.get('longName', symbol))
            currency = info.get('currency', 'USD' if market == MarketType.US else 'HKD')
            
            return QuoteData(
                symbol=symbol, name=name, market=market, currency=currency,
                timestamp=datetime.now(),
                open=float(info.get('open', current_price)), high=float(info.get('dayHigh', current_price)),
                low=float(info.get('dayLow', current_price)), close=float(current_price),
                volume=int(info.get('volume', 0)), amount=None,
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    @classmethod
    def register(cls):
        DataProviderRegistry.register(cls)

YFinanceProvider.register()
