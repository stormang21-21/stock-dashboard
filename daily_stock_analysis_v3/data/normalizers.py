import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
Data Normalizers

Normalize stock data from different providers to standard format.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
import pandas as pd

from loggers import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """
    Normalizes stock data to standard format.
    
    Handles:
    - Column name mapping
    - Data type conversion
    - Currency conversion
    - Timezone normalization
    """
    
    # Standard column names
    STANDARD_COLUMNS = [
        'symbol',
        'name',
        'market',
        'currency',
        'timestamp',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'amount',
    ]
    
    # Common column name mappings from different providers
    COLUMN_MAPPINGS = {
        # AkShare Chinese
        'akshare_cn': {
            '日期': 'timestamp',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
        },
        # Efinance Chinese
        'efinance_cn': {
            '时间': 'timestamp',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
        },
        # Yahoo Finance
        'yfinance': {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        },
    }
    
    def __init__(self, target_currency: str = 'CNY'):
        """
        Initialize normalizer.
        
        Args:
            target_currency: Target currency for conversion
        """
        self.target_currency = target_currency
        self._exchange_rates: Dict[str, float] = {}
    
    def normalize_quote(
        self,
        data: Dict[str, Any],
        source: str = 'unknown',
    ) -> Dict[str, Any]:
        """
        Normalize quote data to standard format.
        
        Args:
            data: Raw quote data
            source: Data source name
            
        Returns:
            Normalized data dictionary
        """
        # Get column mapping for source
        mapping = self.COLUMN_MAPPINGS.get(source, {})
        
        # Create normalized data
        normalized = {}
        
        for key, value in data.items():
            # Map column name
            normalized_key = mapping.get(key, key)
            
            # Convert value
            normalized_value = self._convert_value(normalized_key, value)
            
            normalized[normalized_key] = normalized_value
        
        # Ensure all standard fields present
        for field in self.STANDARD_COLUMNS:
            if field not in normalized:
                normalized[field] = None
        
        # Normalize timestamp
        normalized['timestamp'] = self._normalize_timestamp(normalized['timestamp'])
        
        # Normalize market
        normalized['market'] = self._normalize_market(normalized['market'], normalized['symbol'])
        
        # Convert currency if needed
        if normalized.get('currency') and normalized['currency'] != self.target_currency:
            normalized = self._convert_currency(normalized)
        
        return normalized
    
    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        source: str = 'unknown',
    ) -> pd.DataFrame:
        """
        Normalize DataFrame to standard format.
        
        Args:
            df: Raw DataFrame
            source: Data source name
            
        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df
        
        # Get column mapping
        mapping = self.COLUMN_MAPPINGS.get(source, {})
        
        # Rename columns
        df_normalized = df.rename(columns=mapping)
        
        # Convert data types
        for col in df_normalized.columns:
            if col in ['open', 'high', 'low', 'close', 'amount']:
                df_normalized[col] = pd.to_numeric(df_normalized[col], errors='coerce')
            elif col == 'volume':
                df_normalized[col] = pd.to_numeric(df_normalized[col], errors='coerce').astype('Int64')
            elif col == 'timestamp':
                df_normalized[col] = pd.to_datetime(df_normalized[col], errors='coerce')
        
        # Normalize timestamp column
        if 'timestamp' in df_normalized.columns:
            df_normalized['timestamp'] = pd.to_datetime(df_normalized['timestamp'])
        
        return df_normalized
    
    def _convert_value(self, key: str, value: Any) -> Any:
        """Convert value to appropriate type"""
        if value is None:
            return None
        
        # Numeric fields
        if key in ['open', 'high', 'low', 'close', 'amount', 'volume']:
            try:
                if key == 'volume':
                    return int(float(value))
                else:
                    return float(value)
            except (ValueError, TypeError):
                return None
        
        # String fields
        if key in ['symbol', 'name', 'currency', 'market']:
            return str(value).strip() if value else None
        
        # Timestamp
        if key == 'timestamp':
            return value  # Will be normalized separately
        
        return value
    
    def _normalize_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Normalize timestamp to datetime"""
        if timestamp is None:
            return None
        
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, date):
            return datetime.combine(timestamp, datetime.min.time())
        
        if isinstance(timestamp, str):
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y%m%d",
                "%Y/%m/%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
        
        if hasattr(timestamp, 'to_pydatetime'):
            return timestamp.to_pydatetime()
        
        logger.warning(f"Could not normalize timestamp: {timestamp}")
        return None
    
    def _normalize_market(self, market: Optional[str], symbol: str) -> str:
        """Normalize market identifier"""
        if market:
            market = market.lower()
            if 'cn' in market or 'a' in market:
                return 'cn'
            elif 'hk' in market or 'hong' in market:
                return 'hk'
            elif 'us' in market or 'usa' in market:
                return 'us'
        
        # Infer from symbol
        if symbol:
            symbol = symbol.strip()
            if symbol.isdigit() and len(symbol) == 6:
                return 'cn'
            elif symbol.endswith('.HK'):
                return 'hk'
            elif symbol.endswith('.SS') or symbol.endswith('.SZ'):
                return 'cn'
        
        return 'unknown'
    
    def _convert_currency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert currency to target currency.
        
        Args:
            data: Data dictionary with currency field
            
        Returns:
            Data with converted currency
        """
        source_currency = data.get('currency')
        
        if not source_currency:
            return data
        
        # If already target currency, return
        if source_currency == self.target_currency:
            return data
        
        # Get exchange rate
        rate = self._get_exchange_rate(source_currency, self.target_currency)
        
        if rate is None:
            logger.warning(f"No exchange rate for {source_currency} to {self.target_currency}")
            return data
        
        # Convert numeric fields
        for field in ['open', 'high', 'low', 'close', 'amount']:
            if data.get(field) is not None:
                data[field] = data[field] * rate
        
        data['currency'] = self.target_currency
        
        return data
    
    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Exchange rate or None
        """
        # Check cache
        key = f"{from_currency}_{to_currency}"
        if key in self._exchange_rates:
            return self._exchange_rates[key]
        
        # TODO: Implement actual exchange rate fetching
        # For now, return dummy rates
        dummy_rates = {
            'USD_CNY': 7.2,
            'HKD_CNY': 0.92,
            'CNY_USD': 0.14,
            'CNY_HKD': 1.09,
            'SGD_CNY': 5.3,
            'JPY_CNY': 0.048,
            'CNY_SGD': 0.19,
            'CNY_JPY': 20.8,
            'USD_SGD': 1.35,
            'USD_JPY': 150.0,
        }
        
        rate = dummy_rates.get(key)
        
        if rate:
            self._exchange_rates[key] = rate
        
        return rate
    
    def update_exchange_rates(self, rates: Dict[str, float]) -> None:
        """
        Update exchange rates.
        
        Args:
            rates: Dictionary of exchange rates
        """
        self._exchange_rates.update(rates)
        logger.info(f"Updated {len(rates)} exchange rates")
