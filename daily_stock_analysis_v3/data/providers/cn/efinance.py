"""EFinance Provider - Chinese A-share data"""

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


class EFinanceProvider(BaseDataProvider):
    """Efinance provider for Chinese A-shares"""
    
    name = "efinance"
    description = "Chinese A-share data from efinance"
    supported_markets = [MarketType.CN]
    supported_timeframes = [TimeFrame.DAILY]
    rate_limit = 100
    
    def __init__(self, config=None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import efinance as ef
                self._client = ef
            except ImportError:
                raise DataFetchError("Efinance not installed. Run: pip install efinance", source=self.name)
        return self._client
    
    def get_quote(self, symbol, date=None):
        try:
            ef = self._get_client()
            df = ef.stock.get_quote_history(
                stock_code=symbol,
                beg=(date.strftime("%Y%m%d") if date else "19700101"),
                end=(date.strftime("%Y%m%d") if date else ""),
            )
            
            if df.empty:
                raise DataFetchError(f"No data for {symbol}", source=self.name, symbol=symbol)
            
            row = df.iloc[-1]
            name = self._get_stock_name(symbol)
            
            return QuoteData(
                symbol=symbol, name=name, market=MarketType.CN, currency="CNY",
                timestamp=pd.Timestamp(row['时间']).to_pydatetime(),
                open=float(row['开盘']), high=float(row['最高']), low=float(row['最低']),
                close=float(row['收盘']), volume=int(row['成交量']), amount=float(row['成交额']),
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_history(self, symbol, start_date, end_date, timeframe=TimeFrame.DAILY):
        try:
            ef = self._get_client()
            df = ef.stock.get_quote_history(
                stock_code=symbol,
                beg=start_date.strftime("%Y%m%d"),
                end=end_date.strftime("%Y%m%d"),
            )
            
            if df.empty:
                return []
            
            name = self._get_stock_name(symbol)
            quotes = []
            
            for _, row in df.iterrows():
                quotes.append(QuoteData(
                    symbol=symbol, name=name, market=MarketType.CN, currency="CNY",
                    timestamp=pd.Timestamp(row['时间']).to_pydatetime(),
                    open=float(row['开盘']), high=float(row['最高']), low=float(row['最低']),
                    close=float(row['收盘']), volume=int(row['成交量']), amount=float(row['成交额']),
                ))
            
            return quotes
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_realtime_quote(self, symbol):
        try:
            ef = self._get_client()
            quote = ef.stock.get_realtime_data(symbol)
            
            if quote.empty:
                raise DataFetchError(f"Realtime data not found for {symbol}", source=self.name, symbol=symbol)
            
            row = quote.iloc[0]
            
            return QuoteData(
                symbol=symbol, name=row['股票名称'], market=MarketType.CN, currency="CNY",
                timestamp=datetime.now(),
                open=float(row['开盘价']), high=float(row['最高价']), low=float(row['最低价']),
                close=float(row['现价']), volume=int(row['成交量']), amount=float(row['成交额']),
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def _get_stock_name(self, symbol):
        try:
            ef = self._get_client()
            df = ef.stock.get_stock_name_info([symbol])
            return df.iloc[0]['股票名称'] if not df.empty else symbol
        except:
            return symbol
    
    @classmethod
    def register(cls):
        DataProviderRegistry.register(cls)

EFinanceProvider.register()
