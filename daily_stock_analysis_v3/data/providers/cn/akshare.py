"""AkShare Provider - Chinese A-share data"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.providers.base import BaseDataProvider, QuoteData, MarketType, TimeFrame, DataProviderRegistry
from exceptions import DataFetchError


class AkShareProvider(BaseDataProvider):
    """AkShare provider for Chinese A-shares"""
    
    name = "akshare"
    description = "Chinese A-share data from AkShare"
    supported_markets = [MarketType.CN]
    supported_timeframes = [TimeFrame.DAILY]
    rate_limit = 60
    
    def __init__(self, config=None):
        super().__init__(config)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import akshare as ak
                self._client = ak
            except ImportError:
                raise DataFetchError("AkShare not installed. Run: pip install akshare", source=self.name)
        return self._client
    
    def _format_symbol(self, symbol):
        symbol = symbol.strip()
        if symbol.startswith('6'):
            return f"sh{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"sz{symbol}"
        return symbol
    
    def get_quote(self, symbol, date=None):
        try:
            ak = self._get_client()
            formatted = self._format_symbol(symbol)
            
            df = ak.stock_zh_a_hist(
                symbol=formatted,
                period="daily",
                start_date=(date.strftime("%Y%m%d") if date else "19700101"),
                end_date=(date.strftime("%Y%m%d") if date else ""),
                adjust="qfq",
            )
            
            if df.empty:
                raise DataFetchError(f"No data for {symbol}", source=self.name, symbol=symbol)
            
            row = df.iloc[-1]
            name = self._get_stock_name(symbol)
            
            return QuoteData(
                symbol=symbol, name=name, market=MarketType.CN, currency="CNY",
                timestamp=pd.Timestamp(row['日期']).to_pydatetime(),
                open=float(row['开盘']), high=float(row['最高']), low=float(row['最低']),
                close=float(row['收盘']), volume=int(row['成交量']),
                amount=float(row['成交额']) if '成交额' in row else None,
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_history(self, symbol, start_date, end_date, timeframe=TimeFrame.DAILY):
        try:
            ak = self._get_client()
            formatted = self._format_symbol(symbol)
            
            df = ak.stock_zh_a_hist(
                symbol=formatted,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
            
            if df.empty:
                return []
            
            name = self._get_stock_name(symbol)
            quotes = []
            
            for _, row in df.iterrows():
                quotes.append(QuoteData(
                    symbol=symbol, name=name, market=MarketType.CN, currency="CNY",
                    timestamp=pd.Timestamp(row['日期']).to_pydatetime(),
                    open=float(row['开盘']), high=float(row['最高']), low=float(row['最低']),
                    close=float(row['收盘']), volume=int(row['成交量']),
                    amount=float(row['成交额']) if '成交额' in row else None,
                ))
            
            return quotes
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def get_realtime_quote(self, symbol):
        try:
            ak = self._get_client()
            df = ak.stock_zh_a_spot_em()
            mask = df['代码'] == symbol
            
            if not mask.any():
                raise DataFetchError(f"Symbol {symbol} not found", source=self.name, symbol=symbol)
            
            row = df[mask].iloc[0]
            
            return QuoteData(
                symbol=symbol, name=row['名称'], market=MarketType.CN, currency="CNY",
                timestamp=datetime.now(),
                open=float(row['开盘']), high=float(row['最高']), low=float(row['最低']),
                close=float(row['最新价']), volume=int(row['成交量']), amount=float(row['成交额']),
            )
        except Exception as e:
            raise DataFetchError(str(e), source=self.name, symbol=symbol)
    
    def _get_stock_name(self, symbol):
        try:
            ak = self._get_client()
            df = ak.stock_info_a_code_name()
            mask = df['code'] == symbol
            return df[mask]['name'].iloc[0] if mask.any() else symbol
        except:
            return symbol
    
    @classmethod
    def register(cls):
        DataProviderRegistry.register(cls)

AkShareProvider.register()
